# Arquitectura de la Plataforma de Venta de Entradas (Ticketing)

Esta es la documentación técnica y arquitectónica para el proyecto `demo-ticketing`.
Se trata de una plataforma orientada a la venta masiva de entradas para eventos (Ticketera), diseñada desde cero con una arquitectura altamente escalable (mayormente Serverless), orientada a eventos para absorber picos repentinos de tráfico, y con procesamiento en background mediante Kubernetes (EKS).

## 1. Objetivos del Proyecto
*   **Resolver alta concurrencia**: Ventas concurrentes de entradas (`DynamoDB` + bloqueos optimistas o colas `SQS` / `EventBridge`).
*   **Procesamiento Asíncrono y Batch**: Generación de reportes masivos de ventas, PDFs de entradas y envío de e-mails usando trabajadores (workers) en Kubernetes.
*   **Experiencia en Tiempo Real**: Notificaciones Push (Push Notifications) a los clientes sobre sus eventos, cambios de horario o estado de sus entradas.
*   **Observabilidad completa**: Trazabilidad distribuida con `AWS X-Ray` en todos los flujos de la API y monitoreo detallado con métricas y alarmas en `Amazon CloudWatch`.
*   **Cumplimiento de Patrones Avanzados**:
    *   **CQRS (Command-Query Responsibility Segregation)**: Separación estricta de las operaciones de lectura (Query) y escritura (Command). 
    *   **Pub/Sub**: Desacople de procesos secundarios (e.g. notificaciones push/email) del flujo principal de compra.
    *   **Saga (Orquestada)**: Coordinación de transacciones distribuidas en la compra de la entrada (Reservar Asiento -> Pagar -> Emitir Entrada).
    *   **Circuit Breaker**: Resiliencia frente a fallos temporales en servicios externos (ej. pasarelas de pago).

## 2. Componentes de la Arquitectura

### 2.0 Topología de Cuentas (AWS Organizations)
Para garantizar el aislamiento de recursos, la seguridad (Blast Radius) y la gestión centralizada de facturación (consolidada bajo el **Free Tier**), la infraestructura se despliega bajo una organización Multi-Account regida por el servicio **AWS Organizations**.
*   **CollieTech Management (`658947469588`)**: Cuenta administrativa de gobernanza. Se utiliza exclusivamente para orquestar la creación del resto de sub-cuentas y administrar Service Control Policies (SCPs). No aloja cargas de trabajo.
*   **demo-ticketing-auth-backend**: Cuenta esclava dedicada de forma aislada a los recursos de identidad (Cognito, IAM Roles) y a los lambdas de triggers o pre/post sign-up de autenticación.
*   **demo-ticketing-backend**: Cuenta dedicada a alojar el núcleo de la aplicación, bases de datos DynamoDB, el Bus de Eventos y el poder de cómputo Serverless.
### 2.1 Front-End / Consolas
*   Una Single Page Application (SPA), en React/Next.js, alojada en un S3 y distribuida vía CDN (CloudFront) y aplicaciones móviles (iOS/Android) que consumen la misma API.

### 2.2 Seguridad, Autenticación y Autorización (Repositorio: `demo-ticketing-auth-backend`)
*   **Amazon Cognito**: Manejo de Pool de Usuarios (Compradores) y un grupo de Administradores (Productores de eventos).
*   **AWS IAM**: Políticas y roles restrictivos de mínimo privilegio.
*   **AWS WAF**: Protección del API Gateway frente a ataques DDoS (Bot Control, Rate Limiting).

### 2.3 Web App y Client (Repositorios: `demo-ticketing-web` y `demo-ticketing-android`)
*   **Patrón BFF (Backend For Frontend)**: Para evitar que la Web y la App móvil consuman APIs genéricas pesadas o hagan excesivos llamados de red, la plataforma implementará el patrón **BFF**. Se pondrá al frente un Gateway/Servicio intermedio optimizado y dedicado para la Web, y otro moldeado con menor payload exclusivamente para Android. 
*   **`demo-ticketing-web`**: Single Page Application (SPA) construida con **React (Vite), TypeScript y Vanilla CSS** apuntando a una estética premium (Glassmorphism, animations). Estará alojada en S3 + CloudFront en producción simulada. Su BFF particular le entregará los datos ya agregados para listado de eventos.
*   **`demo-ticketing-android`**: Aplicación nativa móvil con la mejor experiencia UX, construida con **Kotlin** nativo y **Jetpack Compose** (Material 3). Consume un BFF optimizado para redes móviles con payloads más reducidos.

### 2.4 Core Transaccional y Lógica de Negocio (Repositorio: `demo-ticketing-backend`)
*Los lenguajes seleccionados para todo el procesamiento Serverless son **Go (Golang)** y **Node.js**, mientras que todos los microservicios offload y batch que se orquestarán en Kubernetes (Minikube) estarán desarrollados en **Java 21**, aprovechando el enorme potencial multi-threading y el ecosistema robusto de la JVM para reportes masivos.*

#### A. Sala de Espera Virtual (Virtual Waiting Room)
Componente periférico que intercepta el tráfico de una entrada antes de que alcance las APIs transaccionales. Emplea un sistema en memoria (ej: Amazon ElastiCache / Redis) para ordenar a los usuarios y asignarles una posición en la fila frente a picos de demanda, permitiéndoles entrar de forma racionada y controlada al checkout (Mitigación total de Flash Crowds).

#### B. Patrón CQRS (Command & Query)
Dado el alto volumen de lecturas (usuarios buscando eventos) frente a las escrituras puntuales y críticas (generación de una orden de compra), el sistema se divide de la siguiente manera:
*   **Command Model (Escrituras)**: Las órdenes de compra (Commands) apuntan vía API Gateway a Lambdas que insertan atómicamente en **Amazon DynamoDB**. Usamos Step Functions para el ciclo de vida complejo de las mutaciones.
*   **Query Model (Lecturas)**: Un flujo secundario proyecta los eventos de DynamoDB Streams (Pub/Sub) hacia una base de datos más óptima para búsquedas y filtros complejos y reportes (por ejemplo, **Amazon Aurora Serverless** o **Amazon OpenSearch / ElasticSearch**). Las Lambdas de lectura leen exclusivamente de aquí, sin tocar ni bloquear las tablas críticas de transacciones (DynamoDB).

#### B. Orquestación SAGA (AWS Step Functions)
*   **Paso 1**: `ReserveTicket` (Sustrae inventario en Redis/Dynamo - Command).
*   **Paso 2**: `ProcessPayment` (Simulación de pasarela de pagos. Aplica **Circuit Breaker**).
*   **Paso 3**: Si falla el pago, compensa -> `ReleaseTicket` para liberar el bloqueo de asiento a otros usuarios.
*   **Paso 4**: Si el pago es exitoso, emite evento `TicketPurchased`.

#### C. Asincronía, Eventos (PUB/SUB) y Notificaciones Push
*   **Amazon EventBridge**: Bus de eventos central de la plataforma corporativa.
*   Al emitirse el evento `TicketPurchased` o `EventDelayed`, diferentes procesos (Lambdas o Colas) detonan en paralelo:
    *   Una Lambda que inyecta en **Amazon Pinpoint / SNS** para emitir **Notificaciones Push** (Push Notifications SMS/Firebase) a la App del cliente y envío de Email (`Amazon SES`).
    *   Un SQS Queue para alimentar al motor en background de reportística.

#### D. Worker Batch y Procesamiento Intenso (Orquestación en Kubernetes - Java 21)
*   **Amazon EKS (Elastic Kubernetes Service)**:
    *   Procesos muy pesados asíncronos que no caben en Lambdas: Generación de consolidado contable en Excel/CSV, procesamiento de videos o imágenes de los "flyers" del evento, generación batch de los millares de PDFs con códigos QR asegurados con firmas criptográficas.
    *   Para estas tareas se emplearán microservicios estructurados en **Java 21** optimizados para cargas batch.
    *   **KEDA**: Kubernetes Event-driven Autoscaling, que lanza Pods reactivamente cuando se acumulan mensajes en la cola de SQS. Una vez terminados, envía el archivo al **Amazon S3**.

## 3. Observabilidad & Trazabilidad
*   **AWS X-Ray**: Habilitado en **API Gateway**, **Lambda** y **Step Functions**, permitiendo trazar cuánto tarda en procesarse un ticket "end-to-end", visualizando los cuellos de botella exactos en mapas de servicios.
*   **CloudWatch**: Alarmas configuradas por umbrales (Ej: "Si un Circuit Breaker supera 50 fallos contiguos, alertar"). Metrics personalizadas para el negocio, como "TicketsVendidos" o "PagosRechazados".

---
*Este ecosistema garantiza cumplir con las expectativas de sistemas High-Traffic o Flash-Sales de la vida real mediante cloud-native serverless, sumado al músculo crudo de Kubernetes, patrones avanzados (SAGA, CQRS, PUB/SUB, Circuit Breaker) y visibilidad de grado empresarial.*

## 4. Diagramas Visuales (AWS18)
Todos los esquemas visuales y flujogramas de arquitectura se encuentran almacenados y estructurados bajo la notación oficial visual de AWS18 dentro de este repositorio:

*   ▶ **[Diagrama 01: El Flujo Transaccional de Compra (SAGA/Circuit Breaker)](./diagrams/01_FLUJO_DE_COMPRA.md)**
*   ▶ **[Diagrama 02: C4 de Contexto del Sistema de Ticketera](./diagrams/02_C4_CONTEXT.md)**
*   ▶ **[Diagrama 03: Flujo de Login y Autenticación Cognito con JWT](./diagrams/03_AUTH_LOGIN.md)**
*   ▶ **[Diagrama 04: Estrategia de Sala de Espera Virtual (Queue/Flash Crowd)](./diagrams/04_WAITING_ROOM.md)**
