# Estrategia Exhaustiva de Pruebas (Testing Strategy)

Para cumplir con los estándares Enterprise y garantizar la robustez frente a escenarios críticos (como *Flash Crowds* o fallas de pasarela), el ciclo de vida del desarrollo de `demo-ticketing` incorpora desde el Día 0 una matriz de pruebas que abarca mútiples cuadrantes de calidad.

Dada la arquitectura hexagonal, nuestras aserciones y "mocks" se ejecutan al nivel lógico sin depender irremediablemente de la infraestructura viva (AWS).

---

## 1. Pruebas Unitarias (Unit Testing)
Enfoque: **TDD (Test-Driven Development) sobre el Core Hexagonal**.
- **Herramientas Previstas**: `Jest` o `Vitest` (Node.js), `testing` o `testify` (Golang) para Serverless. Para Workers ECS Fargate (Java 21), se utilizará `JUnit 5` y `Mockito`.
- **Cobertura Objetivo**: Mínimo 85% sobre el dominio lógico (Use Cases, Entities).
- **Alcance Funcional**:
  - Validar lógica de negocio del carrito (descuentos, reglas paramétricas).
  - Validar el **Manejador SAGA** de orquestación de Step Functions (probando qué output de estado genera cada Lambda individual).
  - **Mocks estrictos** sobre Capas Port: Todos los SDKs (`DynamoDbClient`, `EventBridgeClient`, `Redis/ElastiCache`). El test de `ReservarAsiento` no debe tocar base de datos.
- **Circuit Breaker**: Pruebas explícitas verificando las transiciones de estado de cerrado, abierto, semi-abierto.

## 2. Pruebas de Integración y Regresión
Enfoque: **Asegurar que las Lambdas y la nube interactuán bajo contrato estricto sin romper desarrollos pasados.**
- **Entorno**: Se correrán predominantemente utilizando **AWS SAM Local** + **LocalStack**. Las pruebas dispararán _Eventos y Payloads_ simulados idénticos a los del `API Gateway` directamente contra el handler.
- **Pruebas de Regresión Continua (CI/CD)**: Cada _Pull Request_ levantará las pruebas unitarias y de integración del microservicio involucrado usando **GitHub Actions**. El código no será promovido (Merge) a `main` si alguna aserción antigua se rompe (evitando regresiones fantasma).
- **Contratos (Pact Testing)**: Verificación de contrato entre el Microservicio _Core_ que arma órdenes y el Worker en AWS ECS Fargate que produce facturas/PDFs leyendo de SQS, asegurando que todos procesan el mismo esquema JSON.

## 3. Pruebas de Alta Concurrencia (Load / Stress Testing)
El requisito más crítico de cualquier sistema "Ticketera" es sobrevivir a instantes masivos de usuarios concurrentes sin originar sobreventas, carreras de base de datos o latencias fatales por Timeouts.

- **Herramientas de Estrés**: **Artillery.io** o **k6** (Grafana).
- **Simulación Carga**: Rampa progresiva y "Spike Testing" repentino de miles de usuarios intentando adquirir el mismo asiento.
- **Validaciones Críticas**:
  1.  **Bloqueo Optimista**: La base de datos (DynamoDB o Redis) **debe** rechazar el 99.9% de intentos para un mismo "asientoX" reportando el mensaje esperado "Asiento no disponible", comprobando que la condición bloqueadora atómica y las compensaciones SAGA funcionen perfecto under stress.
  2.  **Límite Concurrencia de Lambda (Throttling)**: Aserción verificando que el API Gateway responde `429 Too Many Requests` u encola (SQS) la peticion amablemente, enviando a usuarios una sala de espera si se toca la cuota, sin saturar la DB y caerse el sistema entero (`500 Internal Server Error`).
  3.  **Circuit Breaker (Pasarela Simulada)**: Someter el servidor mock de pagos a cargas letales. Visualizar si nuestro Circuit Breaker efectivamente se abre y aborta transacciones en la red antes de ahogar los workers.
- **Monitoreo Local/Gratuito**: Docker Desktop (para los workers) validando su comportamiento con mensajes en cola SQS contra cuellos de botella, mientras Lambdas arrojan trazas locales a AWS SAM para revisión de latencias medias.

## 4. Auditoría de Seguridad y Pentesting (SecOps)
Dada la criticidad de un negocio que tracciona operaciones de tarjetas de crédito y retiene información PII (Nombres, DNI, Emails de asistentes), la plataforma exige la implementación formal de prácticas de *Security Operations*:

- **Análisis de Vulnerabilidades (SAST/DAST)**: Ejecución automatizada de herramientas como `SonarQube` u `OWASP ZAP` dentro del Pipeline CI/CD. Estas herramientas bloquean los PRs si detectan vulnerabilidades OWASP Top 10 (Ej: SQL/NoSQL Injections o dependencias corruptas en el package.json/go.mod).
- **Auditoría de Dependencias (SCA)**: Chequeos constantes y automatizados usando herramientas como `Snyk` o `Dependabot` embebidos en el control de versiones de Github para monitorear agujeros 0-Day.
- **Pentesting Activo**: Una vez desplegado el código en Staging, se emula un ataque "*Black-Box*" (Caja Negra) y ataques de "*Fuzzing*" y "*Rate-Limiting Explotation*" contra las URLs del API Gateway de `demo-ticketing-backend` para asegurar la estrictez funcional del componente `AWS WAF` y validar que Cognito (`demo-ticketing-auth`) no filtre JWTs alterados.
