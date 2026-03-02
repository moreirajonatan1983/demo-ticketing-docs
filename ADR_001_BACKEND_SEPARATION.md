# ADR 001: Separación de Backend (Go/SAM vs Java/K8s)

## Estado
Aceptado

## Contexto
El proyecto Ticketera Cloud requiere manejar dos tipos de cargas de trabajo muy distintas:
1.  **Transaccional de baja latencia**: Compra de entradas, reserva de asientos y consultas de cartelera. Estas tareas necesitan escalar de cero a miles instantáneamente (Flash Sales).
2.  **Procesamiento asíncrono e intensivo**: Generación masiva de PDFs, procesamiento de colas de notificaciones y gestión de sala de espera con lógica de scheduling.

## Decisión
Hemos decidido dividir el backend en dos repositorios/enfoques tecnológicos distintos:

### 1. `demo-ticketing-backend` (Go + AWS SAM)
*   **Responsabilidad**: Core transaccional, API pública y orquestación SAGA.
*   **Tecnología**: Golang por su baja latencia, inicio en frío (Cold Start) mínimo y tipado estricto.
*   **Despliegue**: Serverless (AWS Lambda, API Gateway, DynamoDB, Step Functions).

### 2. `demo-ticketing-services-backend` (Java 21 + Spring Boot + Kubernetes)
*   **Responsabilidad**: Workers asíncronos (`ticket-worker`, `notification-service`) y servicios con estado/scheduling (`waiting-room-service`).
*   **Tecnología**: Java 21 (JVM) por su robustez en el manejo de hilos para tareas pesadas, ecosistema de librerías para PDF y Spring Boot para el manejo fluido de Redis y SQS.
*   **Despliegue**: Contenedores en Kubernetes (AWS EKS) con auto-escalado KEDA basado en eventos.

## Consecuencias
*   **Pros**:
    *   Especialización tecnológica según el caso de uso.
    *   Escalado independiente del núcleo transaccional frente a los procesos de soporte.
    *   Aislamiento de fallos: un problema en la generación de PDFs no afecta la venta de entradas.
*   **Contras**:
    *   Mayor complejidad en el CI/CD al manejar dos stacks distintos.
    *   Necesidad de duplicar algunas definiciones de dominio (aunque se mitiga con contratos claros vía eventos).
