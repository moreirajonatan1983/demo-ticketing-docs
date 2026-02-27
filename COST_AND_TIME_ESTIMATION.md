# Análisis de Costos (AWS) y Estimación de Tiempos

El presente documento detalla la viabilidad económica y el cronograma de construcción para la Plataforma "Ticketera Cloud".
Al estructurarse sobre un modelo predominantemente **Serverless**, los costos base se rigen por un esquema de "Pago por Uso" (Pay-as-you-go), permitiendo un costo inactivo cercano a cero y altamente predecible bajo el nivel **AWS Free Tier**.

---

## 1. Análisis y Estimación de Costos Mensuales AWS (Producción Simulada)

A efectos de esta estimación, se calcula un volumen de impacto base moderado-alto: **100,000 Transacciones de compras mensuales**, logueos diarios y catálogos vistos.

| Servicio AWS | Tipo de Funcionalidad | Uso Estimado | Costo Estimado (Free Tier/On-Demand) |
| :--- | :--- | :--- | :--- |
| **Amazon Cognito** | Identity & Access (Auth) | 50,000 MAUs (Usuarios Activos Mensuales) | **$0.00** (Free Tier cubre hasta 50k MAUs) |
| **Amazon API Gateway** | Puerta de entrada (REST API) | 1,000,000 Requests/mes | **$0.00** (Free Tier: 1 Millón / mes) |
| **AWS Lambda** | Cómputo C/Q y Procesamiento | 3,000,000 Invocaciones (200ms avg, 512mb RAM) | **$0.00** (Free Tier: 1 Millón inv. + 400.000 GB-segundos) |
| **AWS Step Functions** | Orquestación Saga | 100,000 Ejecuciones / 400.000 Transiciones | **$0.00** (Free Tier: 4,000 transiciones libres. Resto: ~$0.01) |
| **Amazon DynamoDB** | Base de Datos (On-Demand) | 2,000,000 Writes / 5,000,000 Reads | **$0.00 - ~$1.50** (Free Tier: 25GB libres. Consumo WCU/RCU es ínfimo) |
| **Amazon EventBridge** | Bus de Eventos (Pub/Sub) | 200,000 Eventos / mes | **$0.00** (Free Tier: Infinito para fuentes AWS. $1 por millon custom) |
| **Amazon SQS / SNS** | Filas y Notificaciones | 300,000 Operaciones / mes | **$0.00** (Free Tier: 1 Millón / mes) |
| **AWS WAF** | Web Application Firewall | 1 WebACL + 3 Reglas Básico | **~$8.00** (Sin capa gratuita. Costo de regla estático) |
| **Worker (Kubernetes)** | Generación Batch de Reportes | Procesado localmente (Minikube Station) o AWS Fargate bajo demanda ocasional. | **$0.00** (Al procesarse en estación local del dev no incurre en costos EKS). |
| **AWS X-Ray / CloudWatch** | Trazabilidad y Métricas | Retención de 30 días, 1 Dashboard | **$0.00** (Free tier cubre 100,000 trazas recopiladas) |

**Total TCO (Total Cost of Ownership) Estimado Mensual: ~$9.50 USD**
*(Impulsado enteramente por el costo base obligatorio del WAF que no posee capa gratuita. Todo el núcleo crudo de procesamiento se mantiene gratuito en estos volúmenes).*

---

## 2. Estimación de Esfuerzo y Cronograma Mínimo Viable (MVP)

La planificación se enfoca en entregar un núcleo funcional con los patrones aplicados, sin desarrollar interfaces visuales (Front-End) fuera del alcance. 

**Duración Total Estimada:** 4 Semanas de Desarrollo Efectivo / 1 Desarrollador Senior / Cloud Engineer.

### Sprint 1 (Semana 1): Fundaciones y Seguridad
*   **Gestión (Día 1-2):** Organización de Repositorios, AWS Multi-Account, Diseño Arquitectural C4 y Diagramas.
*   **Auth (Día 3-5):** Infraestructura en AWS SAM para Cognito, Pools y Configuración de Clientes OIDC, despliegue del repositorio `demo-ticketing-auth`.

### Sprint 2 (Semana 2): Catálogo y Patrón CQRS
*   **Infra Base (Día 1):** Creación de las Tablas maestras transaccionales en DynamoDB (Commands).
*   **APIs (Día 2-3):** Creación del API Gateway y la Arquitectura Hexagonal de AWS Lambda para operaciones de escritura CRUD en los Eventos.
*   **Queries (Día 4-5):** Implementación de DynamoDB Streams y vista proyectada (CQRS) para lectura veloz de catálogo. 

### Sprint 3 (Semana 3): Transaccionalidad / Ticketera SAGA
*   **Core (Día 1-3):** Máquina de Estados (Step Functions SAGA). Módulo Lambda de Reserva (Bloqueo Atómico en DB), Módulo de Pago Simulado y Módulo de Emisión.
*   **Circuit Breaker (Día 4-5):** Control de tolerancias a fallos interconectada con el Step Functions. Compensación (Rollbacks) sobre el inventario.

### Sprint 4 (Semana 4): Asincronía, Batch y Pulido CI/CD
*   **Pub/Sub (Día 1-2):** Disparo de EventBridge cuando "Ticket=Emitido" -> SQS/SNS -> Email/Push Notifier Lambdas.
*   **K8S Batch (Día 3-4):** Integración de Worker Local (Minikube). Consumer en Go o Node.js que extrae de la cola SQS para simular la generación de cientos de PDF / Reportes Csv y envía a S3 local/en nube.
*   **Testeo & CI/CD (Día 5):** Pruebas E2E de integraciones con SAM Local. Creación de los Workflows de Github Actions. Revisión de gráficas de AWS X-Ray.
