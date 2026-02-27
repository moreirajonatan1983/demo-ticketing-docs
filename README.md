# Ticketera Cloud (Demo Project Docs)

> **Proyecto Práctico de Arquitectura y Desarrollo Nube**
> **Postulante/Autor:** Jonatan Moreira

## 1. Visión del Proyecto
**Ticketera Cloud** resuelve el clásico problema de sistemas de venta masiva de entradas concurrentes (Flash Crowds / Sold-outs en segundos).
Se trata de una solución basada en microservicios, eventos asíncronos y procesamiento distribuido usando un mix entre **AWS Serverless** (Lambda, Step Functions, EventBridge) y contenedores administrados con **Kubernetes** para cargas batch pesadas.

Se aplican explícitamente conceptos de observabilidad (métricas y alarmas en CloudWatch + Trazabilidad en X-Ray) así como patrones consolidados del mercado (Pub/Sub, Saga y Circuit Breaker).

## 2. Mapa de Repositorios

- **[demo-ticketing-docs](./)**: Repositorio actual. Contiene las definiciones estratégicas de arquitectura ([`ARCHITECTURE.md`](./ARCHITECTURE.md)), flujogramas de procesos, diagramas y decisiones.
- **`demo-ticketing-auth`**: Autenticación, Roles, Pool de Usuarios (Compradores y Admins), Seguridad IAM, WAF y pasarela principal de identidades (Cognito).
- **`demo-ticketing-core`**: Núcleo de la plataforma (Catálogo de eventos, Inventario, Flujo de Pago - SAGA -, Workers en K8s para envíos de Emails/Reportes y Bus de Eventos).

## 3. Arquitectura y Tecnologías
Para navegar los patrones y arquitectura de este proyecto, referirse al documento [**Arquitectura Core / Diagramas Visuales**](./ARCHITECTURE.md).

## 4. Gestión del Proyecto, Finanzas y Metodología
- [**Análisis de Costos (AWS Free Tier) y Cronograma Semanal (Estimación)**](./COST_AND_TIME_ESTIMATION.md)
- [**Metodología de Planificación (Enfoque Ágil y Teardown)**](./PLANNING_METHODOLOGY.md)
- [**Estrategia Exhaustiva de Pruebas (Unitarias, Regresión y Alta Concurrencia/Stress)**](./TESTING_STRATEGY.md)
- [**Diseño de Pantallas, UI/UX y Wireflows Front-End**](./ui_design/UI_UX_DESIGN.md)
