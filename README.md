# Ticketera Cloud (Demo Project Docs)

> **Proyecto Práctico de Arquitectura y Desarrollo Nube**

## 1. Visión del Proyecto
**Ticketera Cloud** resuelve el clásico problema de sistemas de venta masiva de entradas concurrentes (Flash Crowds / Sold-outs en segundos).
Se trata de una solución basada en microservicios, eventos asíncronos y procesamiento distribuido usando un mix entre **AWS Serverless** (Lambda, Step Functions, EventBridge) y contenedores administrados con **Kubernetes** para cargas batch pesadas.

Se aplican explícitamente conceptos de observabilidad (métricas y alarmas en CloudWatch + Trazabilidad en X-Ray) así como patrones consolidados del mercado (Pub/Sub, Saga y Circuit Breaker).

## 2. Mapa de Repositorios

- **[demo-ticketing-docs](./)**: Repositorio actual. Contiene las definiciones estratégicas de arquitectura ([`01_ARCHITECTURE.md`](./01_ARCHITECTURE.md)), flujogramas de procesos, diagramas y decisiones.
- **`demo-ticketing-auth-backend`**: Autenticación, Roles, Pool de Usuarios (Compradores y Admins), Seguridad IAM, WAF y pasarela principal de identidades (Cognito).
- **`demo-ticketing-backend`**: Núcleo de la plataforma. Microservicios Serverless para API en **Go / Node.js** (Catálogo, Checkout SAGA) y Workers en **Java 21 (Spring / JVM)** desplegados en Kubernetes para envíos masivos y Reportes.
- **`demo-ticketing-web`**: SPA Web construida en **React + TypeScript + Vanilla CSS**, optimizada con Glassmorphism para la UX de compras de clientes finales.
- **`demo-ticketing-android`**: App móvil nativa B2C en **Kotlin/Jetpack Compose**, consumiendo el Backend y Cognito para la compra y visualización de tickets en celular.

## 3. Arquitectura y Tecnologías
Para navegar los patrones y arquitectura de este proyecto, referirse al documento [**Arquitectura Core / Diagramas Visuales**](./01_ARCHITECTURE.md).

## 4. Gestión del Proyecto, Finanzas y Metodología
- [**Análisis de Costos (AWS Free Tier) y Cronograma Semanal (Estimación)**](./02_COST_AND_TIME_ESTIMATION.md)
- [**Metodología de Planificación (Enfoque Ágil y Teardown)**](./03_PLANNING_METHODOLOGY.md)
- [**Diccionario y Glosario Técnico (Términos Arquitectónicos)**](./04_TECHNICAL_GLOSSARY.md)
- [**Estrategia Exhaustiva de Pruebas (Unitarias, Regresión y Alta Concurrencia/Stress)**](./05_TESTING_STRATEGY.md)
- [**Esquemas de Datos en Base de Datos NoSQL (DynamoDB)**](./07_DATA_SCHEMAS.md)
- [**Diseño de Pantallas, UI/UX y Wireflows Front-End**](./ui_design/UI_UX_DESIGN.md)
- [**Experiencia de Onboarding B2C y Plataforma Backoffice B2B**](./ui_design/ONBOARDING_AND_BACKOFFICE.md)

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

