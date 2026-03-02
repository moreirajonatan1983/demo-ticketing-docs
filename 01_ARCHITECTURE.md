# Arquitectura de la Plataforma de Venta de Entradas (Ticketing)

Esta es la documentación técnica y arquitectónica para el proyecto `demo-ticketing`.
Se trata de una plataforma orientada a la venta masiva de entradas para eventos (Ticketera), diseñada desde cero con una arquitectura altamente escalable (mayormente Serverless), orientada a eventos para absorber picos repentinos de tráfico, y con procesamiento en background mediante contenedores Serverless (AWS ECS Fargate).

## 1. Objetivos del Proyecto
*   **Resolver alta concurrencia**: Ventas concurrentes de entradas (`DynamoDB` + bloqueos optimistas o colas `SQS` / `EventBridge`).
*   **Procesamiento Asíncrono y Batch**: Generación de reportes masivos de ventas, PDFs de entradas y envío de e-mails usando workers en **AWS ECS Fargate** (Java/Spring Boot).
*   **Experiencia en Tiempo Real**: Notificaciones Push a los clientes sobre sus eventos, cambios de horario o estado de sus entradas.
*   **Observabilidad completa**: Trazabilidad distribuida con `AWS X-Ray` en todos los flujos de la API y monitoreo detallado con métricas y alarmas en `Amazon CloudWatch`.
*   **Cumplimiento de Patrones Avanzados**: CQRS, Pub/Sub, Saga Orquestada (Step Functions), Circuit Breaker.

## 2. Componentes de la Arquitectura

### 2.0 Topología de Cuentas (AWS Organizations)
Para garantizar el **aislamiento de recursos**, **seguridad (Blast Radius)** y **facturación consolidada** bajo el Free Tier, la infraestructura se despliega bajo una organización Multi-Account regida por **AWS Organizations**.

| Cuenta | Ambiente | Propósito |
|---|---|---|
| **demo-ticketing-management** | - | Cuenta Raíz / Gobernanza. Orquesta sub-cuentas y SCPs. No aloja workloads. |
| **demo-ticketing-operations-stage** | Stage | Servicios compartidos STAGE: S3 para `.tfstate`, ECR para imágenes Docker. |
| **demo-ticketing-operations-prod** | Prod | Servicios compartidos PROD: S3 para `.tfstate`, ECR para imágenes Docker. |
| **demo-ticketing-auth-stage** | Stage | Cognito User Pool STAGE, IAM Roles, Lambdas de auth triggers. JWTs de Stage aislados de Prod. |
| **demo-ticketing-auth-prod** | Prod | Cognito User Pool PROD, IAM Roles, Lambdas de auth triggers. |
| **demo-ticketing-stage** | Stage | Núcleo de la aplicación STAGE: API Gateway, DynamoDB, Lambdas Core, Step Functions, ECS Fargate Workers. |
| **demo-ticketing-prod** | Prod | Núcleo de la aplicación PROD: API Gateway, DynamoDB, Lambdas Core, Step Functions, ECS Fargate Workers. |
| **demo-ticketing-monitoring-stage** | Stage | Observabilidad STAGE: CloudWatch cross-account, CloudTrail, alarmas y dashboards de STAGE. |
| **demo-ticketing-monitoring-prod** | Prod | Observabilidad PROD: CloudWatch cross-account, CloudTrail, alarmas y dashboards de PROD. |

#### Jerarquía Visual
```
AWS Organizations (Root)
└── demo-ticketing-management          (Governance / Raíz)
    └── OU: demo-ticketing
        ├── demo-ticketing-operations-stage  (tfstate S3 + ECR STAGE)
        ├── demo-ticketing-operations-prod   (tfstate S3 + ECR PROD)
        ├── demo-ticketing-auth-stage        (Cognito + IAM STAGE)
        ├── demo-ticketing-auth-prod         (Cognito + IAM PROD)
        ├── demo-ticketing-stage             (Core App STAGE)
        ├── demo-ticketing-prod              (Core App PROD)
        ├── demo-ticketing-monitoring-stage  (CloudWatch + CloudTrail STAGE)
        └── demo-ticketing-monitoring-prod   (CloudWatch + CloudTrail PROD)
```

#### Estrategia del `.tfstate`
El estado de Terraform de **todos los ambientes** se guarda en la **cuenta Operations** correspondiente:
- `demo-ticketing-operations-stage` → `s3://demo-ticketing-tfstate-stage/`
- `demo-ticketing-operations-prod`  → `s3://demo-ticketing-tfstate-prod/`

Los pipelines de GitHub Actions asumen un rol OIDC en **Operations** para leer/escribir el state, sin necesidad de darles acceso directo a las cuentas de workload.

#### Estrategia de Observabilidad (Log Archive Accounts)
Las cuentas `demo-ticketing-monitoring-stage` y `demo-ticketing-monitoring-prod` actúan como **Log Archive separados por ambiente**:
- **CloudTrail por OU**: Los eventos de API de las cuentas STAGE van a `monitoring-stage`; los de PROD a `monitoring-prod`.
- **CloudWatch cross-account**: Cada cuenta envía sus métricas y logs al Sink correspondiente (`monitoring-stage` o `monitoring-prod`).
- **Aislamiento de alertas**: Las alarmas de STAGE no ruidan las de PROD. Un PagerDuty o SNS distinto prioriza los avisos de PROD.
- **Separación de responsabilidades**: Un operador puede ver logs de su ambiente en `monitoring-*` sin acceso a las cuentas de workload.


*   Una Single Page Application (SPA), en React/Next.js, alojada en un S3 y distribuida vía CDN (CloudFront) y aplicaciones móviles (iOS/Android) que consumen la misma API.

### 2.2 Seguridad, Autenticación y Autorización (Repositorio: `demo-ticketing-auth-backend`)
*   **Amazon Cognito**: Manejo de Pool de Usuarios (Compradores) y un grupo de Administradores (Productores de eventos).
*   **AWS IAM**: Políticas y roles restrictivos de mínimo privilegio.
*   **API Gateway — Protección nativa** (sin costo adicional):
    *   **Throttling / Rate Limiting**: `burstLimit` y `rateLimit` configurados en los Usage Plans de API Gateway para prevenir abusos y DDoS de capa 7.
    *   **Resource Policy**: Allowlist/denylist a nivel de IP o cuenta AWS directamente en API Gateway, sin necesidad de WAF.
    *   **Request Validators**: Validación nativa de headers obligatorios, query strings y schema JSON del body antes de que el request llegue a la Lambda.
    *   **Lambda Authorizer**: Valida el JWT en cada request protegido antes de que se ejecute cualquier lógica de negocio.
    *   **CloudWatch Access Logs**: Registro de todos los accesos para auditoría y detección de patrones anómalos.

### 2.3 Web App y Client (Repositorios: `demo-ticketing-web` y `demo-ticketing-android`)
*   **Patrón BFF (Backend For Frontend)**: Para evitar que la Web y la App móvil consuman APIs genéricas pesadas o hagan excesivos llamados de red, la plataforma implementará el patrón **BFF**. Se pondrá al frente un Gateway/Servicio intermedio optimizado y dedicado para la Web, y otro moldeado con menor payload exclusivamente para Android. 
*   **`demo-ticketing-web`**: Single Page Application (SPA) construida con **React (Vite), TypeScript y Vanilla CSS** apuntando a una estética premium (Glassmorphism, animations). Estará alojada en S3 + CloudFront en producción simulada. Su BFF particular le entregará los datos ya agregados para listado de eventos.
*   **`demo-ticketing-android`**: Aplicación nativa móvil con la mejor experiencia UX, construida con **Kotlin** nativo y **Jetpack Compose** (Material 3). Consume un BFF optimizado para redes móviles con payloads más reducidos.

### 2.4 Core Transaccional y Lógica de Negocio (Repositorio: `demo-ticketing-backend`)
*Los lenguajes seleccionados para todo el procesamiento Serverless son **Go (Golang)** y **Node.js**, mientras que todos los microservicios offload y batch que se orquestarán en AWS ECS (Fargate) estarán desarrollados en **Java 21**. Para más detalles sobre esta decisión, ver [ADR 001: Separación de Backend](./ADR_001_BACKEND_SEPARATION.md).*

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

#### D. Worker Batch y Procesamiento Intenso (Orquestación en AWS ECS Fargate - Java 21)
*   **Amazon ECS (Elastic Container Service) con Fargate**:
    *   Procesos muy pesados asíncronos que no caben en Lambdas: Generación de consolidado contable en Excel/CSV, procesamiento de videos o imágenes de los "flyers" del evento, generación batch de los millares de PDFs con códigos QR asegurados con firmas criptográficas.
    *   Para estas tareas se emplearán microservicios estructurados en **Java 21** optimizados para cargas batch.
    *   **Escalado Automático**: Application Auto Scaling basado en SQS/CloudWatch, que lanza contenedores (Tasks) reactivamente cuando se acumulan mensajes en la cola. Una vez terminados, envía el archivo al **Amazon S3**.

## 3. Observabilidad & Trazabilidad
*   **AWS X-Ray**: Habilitado en **API Gateway**, **Lambda** y **Step Functions**, permitiendo trazar cuánto tarda en procesarse un ticket "end-to-end", visualizando los cuellos de botella exactos en mapas de servicios.
*   **CloudWatch**: Alarmas configuradas por umbrales (Ej: "Si un Circuit Breaker supera 50 fallos contiguos, alertar"). Metrics personalizadas para el negocio, como "TicketsVendidos" o "PagosRechazados".

---
*Este ecosistema garantiza cumplir con las expectativas de sistemas High-Traffic o Flash-Sales de la vida real mediante cloud-native serverless, sumado al músculo crudo de contenedores sin servidor (AWS ECS Fargate), patrones avanzados (SAGA, CQRS, PUB/SUB, Circuit Breaker) y visibilidad de grado empresarial.*

## 4. Diagramas Visuales (AWS18)
Todos los esquemas visuales y flujogramas de arquitectura se encuentran almacenados y estructurados bajo la notación oficial visual de AWS18 dentro de este repositorio:

*   ▶ **[Diagrama 01: El Flujo Transaccional de Compra (SAGA/Circuit Breaker)](./diagrams/01_FLUJO_DE_COMPRA.md)**
*   ▶ **[Diagrama 02: C4 de Contexto del Sistema de Ticketera](./diagrams/02_C4_CONTEXT.md)**
*   ▶ **[Diagrama 03: Flujo de Login y Autenticación Cognito con JWT](./diagrams/03_AUTH_LOGIN.md)**
*   ▶ **[Diagrama 04: Estrategia de Sala de Espera Virtual (Queue/Flash Crowd)](./diagrams/04_WAITING_ROOM.md)**
