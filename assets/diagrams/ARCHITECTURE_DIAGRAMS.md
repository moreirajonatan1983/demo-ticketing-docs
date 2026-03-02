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
cd assets/diagrams/scripts
python3 generate_diagram.py
python3 generate_saga_diagram.py
python3 generate_auth_diagram.py
python3 generate_accounts_diagram.py 
python3 generate_route53_diagram.py
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

---

## 4. Route 53 — DNS, Dominio y Multi-Account Strategy (stage / prod)

Describe cómo el dominio comprado en Route 53 se conecta con los distintos ambientes de AWS. Detalla:
- **Route 53 Hosted Zone** como DNS autoritativo de `dominioacomprar.com`
- **Registros DNS:**
  - `dominioacomprar.com` → ALIAS Apex → CloudFront PROD
  - `www.dominioacomprar.com` → CNAME → CloudFront PROD
  - `api.dominioacomprar.com` → CNAME → API Gateway PROD
  - `api.stage.dominioacomprar.com` → CNAME → API Gateway STAGE
- **ACM** emitiendo certificados wildcard `*.dominioacomprar.com` y `*.stage.dominioacomprar.com` en `us-east-1`
- **WAF** declarado independientemente en cada cuenta AWS (PROD / STAGE)
- **Cuentas AWS PROD y STAGE** completamente aisladas entre sí

### 🖼️ Diagrama AWS
![Route 53 Multi-Account](aws_route53_dns.png)

### 📐 Diagrama Mermaid

```mermaid
graph TD
    User["Client Browser / Mobile"] -->|Request| R53["Route 53\nHosted Zone\ndominioacomprar.com"]

    R53 -->|"ALIAS – dominioacomprar.com"| CF_PROD
    R53 -->|"CNAME – www.dominioacomprar.com"| CF_PROD
    R53 -->|"CNAME – api.dominioacomprar.com"| APIGW_PROD
    R53 -->|"CNAME – api.stage.dominioacomprar.com"| APIGW_STAGE

    subgraph "AWS Account: PROD – us-east-1"
        ACM_PROD["ACM SSL\n*.dominioacomprar.com"]
        CF_PROD["CloudFront PROD"]
        WAF_PROD["WAF PROD"]
        S3_PROD[("S3 SPA PROD")]
        APIGW_PROD["API Gateway PROD"]
        LAMBDA_PROD["Lambdas PROD"]

        ACM_PROD -.-> CF_PROD
        CF_PROD --> WAF_PROD --> S3_PROD
        WAF_PROD --> APIGW_PROD --> LAMBDA_PROD
    end

    subgraph "AWS Account: STAGE – us-east-1"
        ACM_STAGE["ACM SSL\n*.stage.dominioacomprar.com"]
        CF_STAGE["CloudFront STAGE"]
        WAF_STAGE["WAF STAGE"]
        S3_STAGE[("S3 SPA STAGE")]
        APIGW_STAGE["API Gateway STAGE"]
        LAMBDA_STAGE["Lambdas STAGE"]

        ACM_STAGE -.-> CF_STAGE
        CF_STAGE --> WAF_STAGE --> S3_STAGE
        WAF_STAGE --> APIGW_STAGE --> LAMBDA_STAGE
    end
```

---

## Mapa Rápido: Subdominios por Ambiente

| Subdominio | Ambiente | Destino |
|---|---|---|
| `dominioacomprar.com` | PROD | CloudFront → S3 React SPA |
| `www.dominioacomprar.com` | PROD | CloudFront → S3 React SPA |
| `api.dominioacomprar.com` | PROD | API Gateway → Lambdas PROD |
| `stage.dominioacomprar.com` | STAGE | CloudFront → S3 React SPA STAGE |
| `api.stage.dominioacomprar.com` | STAGE | API Gateway → Lambdas STAGE |

---

## 5. AWS Organizations — Topología Multi-Account (9 cuentas)

Diagrama completo de la estructura de cuentas AWS. Detalla:
- **Cuenta `management`** como raíz de gobernanza y SCPs
- **OU `demo-ticketing`**: Única unidad que contiene todas las cuentas del proyecto
- **Operations** (`operations-stage` / `operations-prod`): S3 tfstate + ECR imágenes Docker
- **Auth** (`auth-stage` / `auth-prod`): Cognito, IAM Roles, Auth Lambdas aisladas por ambiente
- **Workloads** (`stage` / `prod`): API Gateway, DynamoDB, Step Functions, ECS Fargate
- **Monitoring** (`monitoring-stage` / `monitoring-prod`): CloudWatch cross-account, CloudTrail + SNS alertas
- Flujo de `tfstate` via GitHub Actions OIDC → Operations
- Flujo de logs/métricas cross-account → Monitoring

### 🖼️ Diagrama AWS
![AWS Multi-Account Topology](aws_multi_account_topology.png)

### 📐 Diagrama Mermaid

```mermaid
graph TD
    ROOT["demo-ticketing-management\n(Governance / Root)"]

    subgraph "OU: demo-ticketing"
        OPS_S["demo-ticketing-operations-stage\ntfstate S3 + ECR"]
        OPS_P["demo-ticketing-operations-prod\ntfstate S3 + ECR"]

        AUTH_S["demo-ticketing-auth-stage\nCognito + IAM + Lambdas"]
        AUTH_P["demo-ticketing-auth-prod\nCognito + IAM + Lambdas"]

        WL_S["demo-ticketing-stage\nAPI GW + DynamoDB + Fargate"]
        WL_P["demo-ticketing-prod\nAPI GW + DynamoDB + Fargate"]

        MON_S["demo-ticketing-monitoring-stage\nCloudWatch + CloudTrail + SNS"]
        MON_P["demo-ticketing-monitoring-prod\nCloudWatch + CloudTrail + SNS"]
    end

    ROOT --> OPS_S & OPS_P & AUTH_S & AUTH_P & WL_S & WL_P & MON_S & MON_P

    OPS_S -. "GitHub Actions OIDC → tfstate" .-> WL_S
    OPS_P -. "GitHub Actions OIDC → tfstate" .-> WL_P

    AUTH_S -- "JWT Validation" --> WL_S
    AUTH_P -- "JWT Validation" --> WL_P

    WL_S -. "Logs/Metrics" .-> MON_S
    WL_P -. "Logs/Metrics" .-> MON_P
    AUTH_S -. "CloudTrail" .-> MON_S
    AUTH_P -. "CloudTrail" .-> MON_P
```

---

## Resumen de las 9 cuentas

| Cuenta | OU | Ambiente | Propósito |
|---|---|---|---|
| `demo-ticketing-management` | Root | - | Gobernanza, SCPs, creación de cuentas |
| `demo-ticketing-operations-stage` | demo-ticketing | Stage | tfstate S3, ECR imágenes Docker |
| `demo-ticketing-operations-prod` | demo-ticketing | Prod | tfstate S3, ECR imágenes Docker |
| `demo-ticketing-auth-stage` | demo-ticketing | Stage | Cognito, IAM, Auth Lambdas |
| `demo-ticketing-auth-prod` | demo-ticketing | Prod | Cognito, IAM, Auth Lambdas |
| `demo-ticketing-stage` | demo-ticketing | Stage | API GW, DynamoDB, Step Functions, Fargate |
| `demo-ticketing-prod` | demo-ticketing | Prod | API GW, DynamoDB, Step Functions, Fargate |
| `demo-ticketing-monitoring-stage` | demo-ticketing | Stage | CloudWatch, CloudTrail, SNS alertas |
| `demo-ticketing-monitoring-prod` | demo-ticketing | Prod | CloudWatch, CloudTrail, SNS alertas |
