# Diagrama de Flujo de Compra (Transaccional Core)

Este diagrama modela la lógica transaccional de la compra de una entrada en la plataforma Ticketera, aplicando los patrones **Saga Orquestada** mediante AWS Step Functions, **Circuit Breaker** para el pago simulado y **Pub/Sub** usando EventBridge y colas de procesamiento asíncrono.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ff9900', 'textColor': '#000', 'fontSize': '14px'}}}%%
flowchart TD
    %% Nodos iniciales (App Web -> API Gateway -> Step Functions)
    User((Usuario/Cliente)) --> |"1. Solicita comprar ticket"| API[API Gateway]
    API --> |"2. Inicia Máquina de Estados"| SF[Step Functions - SAGA Orchestrator]
    
    %% Módulo Step Functions (Patrón Saga)
    subgraph Saga[Transacción de Compra SAGA]
        SF --> L_Reservar[Lambda: ReserveTicket<br/>(Bloqueo Optimista)]
        L_Reservar --> DB_Reserva[(DynamoDB:<br/>Reservar Asiento)]
        L_Reservar -.-> |"Éxito"| L_Pago[Lambda: ProcessPayment]
        
        %% Circuit Breaker del Pago
        subgraph CB[Patrón Circuit Breaker]
            L_Pago --> |"3. Intentar Cobro"| PG{Pasarela Externa Simulada}
            PG --"Aceptado"--> L_Confirmar[Lambda: ConfirmTicket]
            PG --"Timeout/Caída / Circuito Abierto"--> L_Compensacion[Lambda: ReleaseTicket<br/>(Bloqueo Rollback)]
        end
        
        L_Compensacion --> DB_Libera[(DynamoDB:<br/>Liberar Asiento)]
        L_Confirmar --> DB_Confirma[(DynamoDB:<br/>Ticket Pagado)]
    end
    
    %% Módulo Pub/Sub
    subgraph AsincroniaPubSub[Eventos Posteriores (Pub/Sub)]
        DB_Confirma --> |"4. Emite Evento Atómico"| Stream[DynamoDB Streams]
        Stream --> EB[EventBridge Bus: TicketPurchased]
        
        EB --> |"Desacoplado"| Notifier[Lambda: Email/Push]
        Notifier --> SNS_Pinpoint(((Amazon Pinpoint / SNS<br/>Push notification)))
        
        EB --> |"Encola para el Worker"| SQS[Amazon SQS]
        SQS --> KEDA[Minikube Cluster / Worker]
        KEDA --> |"Genera PDF masivo"| S3[(Amazon S3)]
    end
```

> **Nota AWS18**: El equivalente de este esquema visualizado en Draw.io consistirá en íconos oficiales del set "AWS18", donde los rectángulos de Lambda usarán de forma estricta el logotipo naranja de Compute (Lambda), la base de datos de DynamoDB usará el ícono purpura oficial, y las reglas del bus usarán EventBridge.
