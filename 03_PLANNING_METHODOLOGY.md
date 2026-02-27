# Playbook y Metodología de Planificación (Planificación de Proyecto)

Este documento detalla la filosofía y métodología adoptada para la gestión del ciclo de vida del software en el proyecto `demo-ticketing`.
Se evidencia un modelo de trabajo ágil iterativo (Scrum/Kanban) centrado estrictamente en el diseño de sistema previo a la construcción (Design-First) y enfocado en la documentación de Arquitectura y Patrones mediante Decisiones de Arquitectura (ADRs).

## 1. Fases del Proyecto (Waterfall a Ágil)

### Fase 0: Descubrimiento y Diseño (Fase Actual)
Antes de escribir cualquier línea de código, se establecen las fundaciones:
1.  **Levantamiento de Requerimientos Técnicos:** Identificar restricciones de negocio (Alta concurrencia de tickets) y requerimientos tecnológicos (Uso Exclusivo de AWS Free-Tier, Serverless, Patrones CQRS, Saga, Pub/Sub, Kubernetes).
2.  **Arquitectura del Dominio y Diagramado:** (C4 Model).
    *   Nivel Contexto y Nivel Contenedor: Diseñados en Draw.io / Excalidraw, exportados e incrustados en `01_ARCHITECTURE.md`. **Todos los diagramas deben utilizar la especificación y paleta de iconos oficiales de AWS18**.
3.  **Provisión de Entorno AWS Multi-Cuenta:** 
    *   Creación inicial de `AWS Organizations` Accounts aislando dominios lógicos: `demo-ticketing-auth-backend` y `demo-ticketing-backend`. (Garantizando la barrera del "Blast Radius" de seguridad y límites de cuentas *Free-Tier*).

### Fase 1: Setup de Infraestructura y Desarrollo Local
*   **Decisión ADR (Architecture Decision Record)**: Se escoge la herramienta **AWS SAM (Serverless Application Model)** para el desarrollo, simulación local y despliegue del código Serverless hacia `demo-ticketing-backend` y `demo-ticketing-auth-backend`. El desarrollo será estrictamente "Local-First".
*   **Dominio de Seguridad**: Creación del entorno IAM (Mínimo Privilegio) y Cognito (Autenticación) en la nueva cuenta `demo-ticketing-auth-backend`.

### Fase 2: Construcción Central (El "Core" Backend)
*   **Patrones Funcionales**: Se decide la **Arquitectura Hexagonal (Ports & Adapters)** dentro de cada uno de los microservicios/Lambdas core. El Dominio (Ej. Entidades como de Orden/Compra) se aloja en el núcleo abstracto, aislando todas las interacciones de los Frameworks (AWS SDK, Redis, SQS, API Gateway).
*   **TDD y Trazabilidad**: El código backend Serverless (**Node.js y Go**) y los workers Kubernetes (**Java 21**) se desarrollan con el inyector de `AWS X-Ray` activo desde el día uno y tests unitarios a los _UseCases_ de la arquitectura Hexagonal mediante mocks (sin tocar AWS localmente).

### Fase 3: Worker Híbrido y Procesos Asíncronos (Kubernetes)
*   Se diseña el desarrollo del componente Batch masivo de la Ticketera priorizando el desarrollo enteramente sobre ambientes **Minikube** locales.
*   *Nota Free-Tier*: Toda demostración de clústeres orquestadores locales (Workers generando reportes o emitiendo PDFs) en Kubernetes debe ser soportada directamente en la estación de desarrollo con Minikube, sin necesidad de aprovisionar Amazon EKS (Managed Service), validando de forma completamente gratuita el desacople de sistemas basados en KEDA u operadores asíncronos.

## 2. Herramientas de Planificación (Ciclo de Gestión)
El desarrollo y planificación de historias de usuario (Tickets/Issues) seguirá un abordaje profesional similar a Jira/Linear usando **GitHub Projects / Issues**.

### El Tablero Kanban
Cada requerimiento arquitectónico se desagrega en un flujo:
1.  **Backlog Técnico** (Ej. "Diseñar arquitectura SAGA con Step Functions").
2.  **To-Do** (Bajo análisis y diagramación funcional).
3.  **En Progreso** (Codificación IaC/Hexagonal).
4.  **En Revisión / QA** (PR generado en GitHub donde la Acciones CI corren Linters, y Tests Unitarios y despliegan entornos efímeros limpios apoyados en Mocking/LocalStack).
5.  **Listo / Deployado**.

### Políticas de Código (Playbook de Devs)
1.  **Commit Convention**: Se utilizarán prefijos obligatorios (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `arch:`).
2.  **Pull Request Template**: Toda subida a `main` debe contener en la descripción qué patrones fueron aplicados (e.g. "Se aplica Circuit Breaker para..."), validaciones locales e imágenes del Log de `AWS X-Ray` en caso transaccional.
3.  **Arquitectura Hexagonal Estricta**: Las llamadas que utilizan las dependencias a los servicios AWS (Puertos Adaptadores "Driven") como `DynamoDBClient` nunca deben estar incrustadas en el Caso de Uso o Lógica del modelo. Todos se inyectan como inferfaz al inicializar el handler de la Función Lambda.

## 3. Manejo Estratégico del Free Tier
Asegurar que todas las opciones presenten una facturación virtual de `$0.00`:
*   **Lambda, SQS y SNS**: Generosos dentro del capa gratuita (1 millon / 1 millon por mes). Emulados en local con AWS SAM CLI previo al salto.
*   **DynamoDB y Aurora Min-Capacity**: Se utilizará facturación de capacidad "On-Demand" asegurando que las pruebas de concurrencia CQRS y Saga limiten drásticamente el costo al volumen exacto procesado y no paguen RCU/WCU inactivo de base de datos encendida. Emulación con `DynamoDB Local` donde se pueda.
*   **Kubernetes (Minikube)**: Ausencia absoluta de costos por el orquestador o Control Plane gracias a operar localmente. Evita el costo mínimo de ~72$ USD mensuales de Amazon EKS, cumpliendo el requerimiento de evaluación bajo costo Cero de la autoevaluación simulando los Workers en la estación de trabajo.
*   **Teardown Automático**: Todas las plantillas de Infraestructura desplegadas en las cuentas provisionadas por Management (`AWS Organizations`) con SAM CLI estarán contenidas en ambientes (`sam deploy --no-confirm-changeset`) fácilmente destructibles con `sam delete` al cierre de cualquier jornada.
