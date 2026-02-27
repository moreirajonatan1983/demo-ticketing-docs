# Ticketera Cloud (Demo Project Docs)

> **Proyecto Práctico de Arquitectura y Desarrollo Nube**
> **Postulante/Autor:** Jonatan Moreira

## 1. Visión del Proyecto
**Ticketera Cloud** resuelve el clásico problema de sistemas de venta masiva de entradas concurrentes (Flash Crowds / Sold-outs en segundos).
Se trata de una solución basada en microservicios, eventos asíncronos y procesamiento distribuido usando un mix entre **AWS Serverless** (Lambda, Step Functions, EventBridge) y contenedores administrados con **Kubernetes** para cargas batch pesadas.

Se aplican explícitamente conceptos de observabilidad (métricas y alarmas en CloudWatch + Trazabilidad en X-Ray) así como patrones consolidados del mercado (Pub/Sub, Saga y Circuit Breaker).

## 2. Mapa de Repositorios

- **[demo-ticketing-docs](./)**: Repositorio actual. Contiene las definiciones estratégicas de arquitectura ([`ARCHITECTURE.md`](./ARCHITECTURE.md)), flujogramas de procesos, diagramas y decisiones.
- **`demo-ticketing-auth-backend`**: Autenticación, Roles, Pool de Usuarios (Compradores y Admins), Seguridad IAM, WAF y pasarela principal de identidades (Cognito).
- **`demo-ticketing-backend`**: Núcleo de la plataforma. Microservicios Serverless para API en **Go / Node.js** (Catálogo, Checkout SAGA) y Workers en **Java 21 (Spring / JVM)** desplegados en Kubernetes para envíos masivos y Reportes.
- **`demo-ticketing-web`**: SPA Web construida en **React + TypeScript + Vanilla CSS**, optimizada con Glassmorphism para la UX de compras de clientes finales.
- **`demo-ticketing-android`**: App móvil nativa B2C en **Kotlin/Jetpack Compose**, consumiendo el Backend y Cognito para la compra y visualización de tickets en celular.

## 3. Arquitectura y Tecnologías
Para navegar los patrones y arquitectura de este proyecto, referirse al documento [**Arquitectura Core / Diagramas Visuales**](./ARCHITECTURE.md).

## 4. Gestión del Proyecto, Finanzas y Metodología
- [**Análisis de Costos (AWS Free Tier) y Cronograma Semanal (Estimación)**](./COST_AND_TIME_ESTIMATION.md)
- [**Metodología de Planificación (Enfoque Ágil y Teardown)**](./PLANNING_METHODOLOGY.md)
- [**Diccionario y Glosario Técnico (Términos Arquitectónicos)**](./TECHNICAL_GLOSSARY.md)
- [**Estrategia Exhaustiva de Pruebas (Unitarias, Regresión y Alta Concurrencia/Stress)**](./TESTING_STRATEGY.md)
- [**Diseño de Pantallas, UI/UX y Wireflows Front-End**](./ui_design/UI_UX_DESIGN.md)
- [**Experiencia de Onboarding B2C y Plataforma Backoffice B2B**](./ui_design/ONBOARDING_AND_BACKOFFICE.md)
