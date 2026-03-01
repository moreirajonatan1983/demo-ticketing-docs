# Diagramas de Arquitectura (Mermaid)

Este documento contiene los diagramas de arquitectura de nuestra plataforma, utilizando formato **Mermaid** (soportado nativamente por GitHub).

## 1. Arquitectura de Despliegue General en AWS

Este diagrama ilustra cómo las solicitudes de los usuarios entran desde el navegador y viajan a través del ecosistema AWS en el backend Serverless y Docker ECS Fargate de larga duración.

```mermaid
graph TD
    %% Entidades Externas
    User(Web Browser App React) -->|1. HTTP / GET SPA| CloudFront[AWS CloudFront CDN]
    CloudFront --> S3Frontend[(S3 Bucket Web Dist)]
    
    User -->|2. REST / JSON| APIGW[AWS API Gateway]
    
    %% API Gateway Flow
    subgraph "demo-ticketing-auth-backend"
        APIGW -- "{proxy+} + Headers" --> CustomAuthorizer(Lambda: Go Custom Authorizer JWT)
        APIGW -- "POST /auth" --> TokenGenerator(Lambda: Go Auth Generator)
    end
    
    %% Serverless Backend - Core APIs
    subgraph "demo-ticketing-backend (Serverless CORE)"
        APIGW -->|Proxy| EventsLambda(Lambda: Events Serverless Go)
        APIGW -- "Authorized" --> TicketsLambda(Lambda: Tickets Serverless Go)
        APIGW -- "Authorized" --> SeatsLambda(Lambda: Seats Concurrency Logic)
        APIGW -- "Authorized" --> CheckoutLambda(Lambda: Checkout SAGA Orchestrator)
        
        %% Core Data Bases
        EventsLambda -.-> DynamoDBEvents[(DynamoDB Events/Shows)]
        SeatsLambda -.-> DynamoDBSeats[(DynamoDB Optimistic Locks)]
        TicketsLambda -.-> DynamoDBTickets[(DynamoDB Transaccional)]
        CheckoutLambda -.-> StepFunctions[AWS Step Functions: SAGA]
    end

    %% Tareas Asincronas y Workers Fargate
    subgraph "demo-ticketing-services-backend (AWS Fargate Workers)"
        StepFunctions -.->|Event EventBridge| SQSQueue[(AWS SQS: TicketPurchased)]
        SQSQueue -.->|Polled Auto-escalado de 0 a N Tasks| WorkerFargate[Amazon ECS Fargate: Java Spring Boot]
        WorkerFargate -.->|Generación QR PDF| S3Tickets[(S3 Docs Tickets Bucket)]
    end

    %% Styles
    classDef lambda fill:#f96,stroke:#333,stroke-width:2px;
    classDef db fill:#00d,color:#fff,stroke:#333,stroke-width:2px;
    classDef cdn fill:#0cf,stroke:#333,stroke-width:2px;
    classDef queue fill:#f00,color:#fff,stroke:#333,stroke-width:2px;
    classDef fargate fill:#090,color:#fff,stroke:#333,stroke-width:2px;
    
    class EventsLambda,SeatsLambda,CheckoutLambda,TicketsLambda,CustomAuthorizer,TokenGenerator lambda;
    class DynamoDBEvents,DynamoDBSeats,DynamoDBTickets,S3Frontend,S3Tickets db;
    class CloudFront cdn;
    class SQSQueue queue;
    class WorkerFargate fargate;
```

---

## 2. Flujo de Transacción SAGA (Proceso de Checkout y Compensaciones)

Describe el mecanismo Core de compra de Ticketera: un patrón de microservicios distribuido "Saga" (Orquestado por Step Functions y Lambda), garantizando consistencia atómica sin bloquear registros globalmente (Optimistic Locking).

```mermaid
sequenceDiagram
    participant Frontend as Web Client
    participant API as API Gateway (Proxy)
    participant Func as AWS Step Functions
    participant Checkout as Checkout Lambda
    participant Seats as Seats Lambda
    participant Payment as External Bank API
    participant Tickets as Tickets Lambda

    Frontend->>API: POST /checkout (userId, eventId, seats, token)
    API->>Checkout: Invoca API EndPoint
    Checkout->>Func: Start Execution (SAGA Event)
    Func->>Seats: Intenta Lock Asiento Otimista (Verificar DB)
    
    alt Asientos Ocupados
        Seats-->>Func: Error: "Seat already taken"
        Func->>Frontend: Response 409 Conflict (Pérdida de puja de red)
    else Asientos Libres
        Seats-->>Func: Success: Cambia a "RESERVED"
        Func->>Payment: Invoca Pago / Auth de Tarjeta
        
        alt Pago Denegado (Tarjeta sin Saldo)
            Payment-->>Func: Error Payment
            Func->>Seats: SAGA COMPENSATING ACTION: Cambiar "RESERVED" a "AVAILABLE" !!
            Func->>Frontend: Return 402 Payment Required
        else Pago Exitoso
            Payment-->>Func: Payment Authorized (TxId)
            Func->>Seats: Actualiza a "SOLD" Definitivo
            Func->>Tickets: Genera Metadata Básica del Ticket en DB
            Tickets-->>Func: Ticket_Generated_Event
            Func->>Frontend: Return 200 OK
        end
    end
```

---

## 3. Patrón de Diseño Hexagonal (Arquitectura Limpia y Go Lambdas)

Visión de la estructura interna del código en Golang del backend Core y Auth (Puertos y Adaptadores).

```mermaid
graph LR
    %% Actores Externos (Adaptadores Primarios)
    ActorAPI(AWS API Gateway) -. HTTP POST .-> APIHandler[Adapter: API Handler REST]
    ActorCLI(AWS CLI Local) -. Invoke Event .-> APIHandler

    %% Núcleo (Hexágono)
    subgraph "Hexágono: Lógica de Dominio Central (Aislada)"
        APIHandler -. "Usa" .-> ServiceInteface{{Port: Token Service Interface}}
        ServiceInteface -. "Implementado por" .-> BusinessService[Core Logic: Domain Model + Token Maker]
        BusinessService -. "Retorna" .-> JWTModel[Domain: User Claims Object]
    end

    %% Adaptadores Secundarios Externos (Data / Services)
    BusinessService -. "Usa" .-> RepositoryPort{{Port: DynamoDB Adapter Interface}}
    RepositoryPort -. "Implementado por" .-> DynamoDBLogic[Secondary Adapter: AWS SDK DynamoDB]
    DynamoDBLogic -. Query .-> TrueDB[(Dynamo Cloud DB)]
    
    %% Styles
    classDef ext fill:#ddd,stroke:#333;
    classDef inter fill:#fcf,stroke:#333,stroke-width:2px,shape:hexagon;
    classDef dom fill:#ffc,stroke:#333;
    
    class ActorAPI,ActorCLI,TrueDB ext;
    class ServiceInteface,RepositoryPort inter;
    class BusinessService,JWTModel dom;
```
