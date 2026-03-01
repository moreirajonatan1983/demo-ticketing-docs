# Diagramas de Arquitectura

Este documento contiene los diagramas de arquitectura de la plataforma `demo-ticketing`.

Cada sección incluye **dos formatos**:
- 🖼️ **Diagrama PNG con íconos AWS oficiales** (generado con la librería `diagrams` de Python + Graphviz)
- 📐 **Diagrama Mermaid** (para edición rápida inline directamente en GitHub)

**Región principal:** `us-east-1` (N. Virginia) — *Reason: mayor disponibilidad de servicios Free Tier y latencia optimizada para LATAM.*

---

## Requisitos para regenerar los diagramas PNG

```bash
brew install graphviz
python3 -m venv venv && source venv/bin/activate
pip install diagrams
python3 generate_diagram.py
python3 generate_saga_diagram.py
python3 generate_auth_diagram.py
```

## 1. Arquitectura de Despliegue General en AWS

Este diagrama ilustra cómo las solicitudes de los usuarios fluyen desde el browser a través de **WAF → CloudFront → API Gateway** hacia los distintos microservicios. Detalla:
- **Región:** `us-east-1`, **AZ:** `us-east-1a` y `us-east-1b`
- **WAF** para protección OWASP en borde
- **CloudFront** para CDN del Frontend SPA
- **API Gateway** como único punto de entrada
- **Lambdas Go** para lógica de Auth y APIs Core
- **ECS Fargate** para workers Java de larga duración
- **DynamoDB** (multi-AZ) para almacenamiento NoSQL
- **EventBridge + SQS** como bus de eventos asíncronos

### 🖼️ Diagrama AWS
![AWS General Architecture](aws_general_architecture.png)

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

Describe el mecanismo Core de compra de Ticketera: un patrón de microservicios distribuido "Saga" (Orquestado por Step Functions y Lambda), garantizando consistencia atómica sin bloquear registros globalmente (Optimistic Locking). Detalla:
- **Región:** `us-east-1`, **AZ:** `us-east-1a` (transaccional) y `us-east-1b` (async workers)
- **Compensating Actions** en caso de fallo de pago
- **DynamoDB** Optimistic Lock para asientos
- **SQS + ECS Fargate** para procesamiento asincrónico tras el pago exitoso

### 🖼️ Diagrama AWS
![SAGA Checkout Flow](aws_saga_flow.png)

### 📐 Diagrama Mermaid
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

## 3. Auth & Security Flow

Visualiza el flujo de autenticación y autorización de la plataforma de extremo a extremo. Detalla:
- **WAF** como primer filtro OWASP en borde
- **CloudFront** como capa intermedia distribuidora de peticiones
- **API Gateway** enrutando a las Lambdas especializadas de Auth
- **Custom Authorizer** (Go/Hexagonal) validando JWT en cada request protegido
- **Secrets Manager** almacenando el secreto `JWT_SECRET` de forma segura
- **Cognito** preparado para futura integración de SSO/Active Directory

### 🖼️ Diagrama AWS
![Auth & Security Flow](aws_auth_flow.png)

### 📐 Diagrama Mermaid (Hexagonal Architecture)
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
