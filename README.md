# Ticketera Cloud

> **Plataforma de Venta Masiva de Entradas**

## 1. Visión del Producto y Negocio
**Ticketera Cloud** es una solución diseñada para gestionar la venta masiva de entradas a eventos de muy alta demanda. Su objetivo principal es garantizar una experiencia de compra fluida y transparente para los fans, incluso durante picos extremos de tráfico mundial (flash crowds y sold-outs en segundos).

### Propuesta de Valor
- **Experiencia de Usuario (UX) sin fricciones**: Interfaz intuitiva, ágil y atractiva para que los usuarios aseguren sus entradas en pocos pasos y sin demoras.
- **Confiabilidad ante alta demanda**: La plataforma mantiene su estabilidad cuando miles de usuarios entran a comprar al mismo tiempo. Se implementan filas virtuales justas y reserva de tickets temporal.
- **Gestión Integral para Promotores (B2B)**: Un panel de control (Backoffice) completo para crear eventos, configurar zonas y capacidades, además de analizar métricas de ventas en tiempo real.
- **Acceso Omnicanal**: Disponibilidad equitativa a través de plataforma web y aplicación móvil nativa.

## 2. Visión Técnica y Arquitectura
Para lograr cumplir con las demandas del negocio sin comprometer la estabilidad, la plataforma se apoya bajo el capó en una arquitectura de microservicios elástica. Utiliza un ecosistema híbrido entre **AWS Serverless** (Lambda, Step Functions, EventBridge) para transacciones ultra-rápidas, y contenedores administrados (como **Kubernetes**) para cargas más pesadas o procesos batch.

Se aplican patrones de diseño distribuidos como *Saga* (para asegurar compras exactas sin problemas de consistencia) y *Circuit Breaker*. Todo esto rodeado de una fuerte estrategia de observabilidad y telemetría.

Para detalles profundos y flujogramas, referirse al documento [**Arquitectura Core / Diagramas Visuales**](./01_ARCHITECTURE.md).

## 3. Mapa de Repositorios

El proyecto está organizado en los siguientes grandes módulos:

- **[demo-ticketing-docs](./)**: Este repositorio. Contiene la visión B2B/B2C, planes de proyecto, diseños de interfaz (UI/UX) y decisiones de arquitectura.
- **`demo-ticketing-auth-backend`**: Gestión de Identidad y Seguridad. Autenticación, roles y reglas de acceso unificadas usando AWS Cognito.
- **`demo-ticketing-services-backend`**: El motor del negocio. Microservicios transaccionales en **Go / Node.js** (Catálogo de eventos, Checkout de compras) y Workers en **Java 21 (Spring / JVM)** para envíos masivos de tickets y reportes financieros.
- **`demo-ticketing-web`**: Solución web para clientes y promotores. SPA construida en **React + TypeScript**, enfocada en ofrecer una estética premium (Glassmorphism) y alta velocidad.

## 4. Documentación y Gestión de Proyecto

Explora los siguientes documentos funcionales y técnicos para sumergirte en el proyecto:

- [**Diseño de Pantallas, UI/UX y Wireflows Front-End**](./ui_design/UI_UX_DESIGN.md)
- [**Experiencia de Onboarding B2C y Plataforma Backoffice B2B**](./ui_design/ONBOARDING_AND_BACKOFFICE.md)
- [**Diccionario y Glosario (Funcional y Técnico)**](./04_TECHNICAL_GLOSSARY.md)
- [**Estrategia Exhaustiva de Pruebas**](./05_TESTING_STRATEGY.md)
- [**Metodología de Planificación (Enfoque Ágil)**](./03_PLANNING_METHODOLOGY.md)
- [**Análisis de Costos (AWS) y Cronograma Semanal**](./02_COST_AND_TIME_ESTIMATION.md)
- [**Esquemas de Datos en Base de Datos NoSQL (DynamoDB)**](./07_DATA_SCHEMAS.md)

## 5. Implementación MVP Finalizada ✅
A lo largo de múltiples iteraciones, el MVP demostrativo de este proyecto completó con éxito el **100% de las historias de usuario planificadas**:
1. **Transacciones Resilientes**: Implementación asíncrona mediante un patrón **SAGA Core (Step Functions)** para retenciones, compensaciones de inventario y resolución de compras. DLQs creados para eventos erróneos de mensajería (SQS).
2. **Kubernetes Java Workers**: Despliegue de los servicios offload en Minikube Java 21 (`worker`, `waiting-room`, `notification`). KEDA incorporado para Serverless Autoscaling junto con observabilidad local interceptada por **Prometheus + Grafana PodMonitors y Actuators**.
3. **Observabilidad Distribuida**: Instrumentación y tracing logradas nativamente inyectando el AWS X-Ray SDK directamente sobre el código nativo Golang y los adaptadores DynamoDB de los Lambdas.
4. **Front-End Premium**: Una Web App full conectada al backend con login social integrado (Cognito), colas virtuales interactivas, componentes de selección visual de asientos optimizados y control visual Glassmorphism para la cartelera.
5. **CI/CD Integrado**: Pipelines creados e implementados enteramente con GitHub Actions para Go Lambdas y Build+Deploy en K8s para Java, utilizando autenticación segura sin credenciales duras.

## 6. Prompt para Agentic AI (Setup inicial en nueva Mac)

Si necesitas continuar el desarrollo de este proyecto en una nueva Mac utilizando un Agente IA (como Antigravity), puedes proporcionarle el siguiente **prompt** para que configure todo el entorno de forma automatizada:

---
**Prompt sugerido para el Agente:**

> "Eres un ingeniero DevOps y desarrollador Full-Stack. Necesito que prepares mi entorno de desarrollo local en esta Mac para poder trabajar en el proyecto «demo.ticketing».
> 
> **1. Instalación de Dependencias y Herramientas**
> Utiliza Homebrew (`brew`) para verificar e instalar las siguientes herramientas fundamentales para la arquitectura del proyecto:
> - `git` (Control de versiones)
> - `awscli` (AWS CLI para Serverless)
> - `terraform` (Para la infraestructura como código / API Gateway / IAM)
> - `node` (Node.js LTS para la Web App React/TS)
> - `go` (Para los microservicios Serverless en Golang)
> - `openjdk@21` y `maven` (Java 21 para los Workers en Spring Boot)
> - `minikube` y `kubectl` (Para probar despliegues locales de los workers en K8s)
> - (Nota: Asume que ya proveeré un runtime de contenedores como Docker Desktop u OrbStack, o pídeme que lo instale si no está disponible).
> 
> **2. Clonado de Repositorios**
> Crea un directorio de trabajo (por ejemplo `~/developer/proyectos/demo`) y accede a él. Luego, clona los siguientes repositorios de mi organización/usuario de GitHub (`moreirajonatan1983`):
> 1. `https://github.com/moreirajonatan1983/demo-ticketing-docs.git`
> 2. `https://github.com/moreirajonatan1983/demo-ticketing-auth-backend.git`
> 3. `https://github.com/moreirajonatan1983/demo-ticketing-services-backend.git`
> 4. `https://github.com/moreirajonatan1983/demo-ticketing-web.git`
> 
> **3. Inicialización (Opcional)**
> Una vez descargados, entra a la carpeta de `demo-ticketing-web` y ejecuta el comando necesario para instalar las dependencias de Node (`npm install` o `yarn`). Además, lista los directorios para confirmar que todos los repositorios se clonaron correctamente.
> 
> Por favor, infórmame paso a paso lo que vas instalando y si te encuentras con algún problema de permisos o dependencias."
---
