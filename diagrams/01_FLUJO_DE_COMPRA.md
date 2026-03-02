# Diagrama de Flujo de Compra (Transaccional Core)

Este diagrama modela la lógica transaccional de la compra de una entrada en la plataforma Ticketera, aplicando los patrones **Saga Orquestada** mediante AWS Step Functions, **Circuit Breaker** para el pago simulado y **Pub/Sub** usando EventBridge y colas de procesamiento asíncrono.

```mermaid
architecture-beta
    group api(cloud)[API & Entrypoint]
    group saga(cloud)[SAGA Orchestrator]
    group worker(cloud)[K8s Workers]
    group data(cloud)[Databases]

    service web(internet)[Client SPA] in api
    service gateway(api-gateway)[API Gateway] in api
    service sf(step-functions)[Step Functions] in saga
    
    service l1(lambda)[saga-reserve-seat] in saga
    service l2(lambda)[saga-process-payment] in saga
    service l3(lambda)[saga-release-seat] in saga
    service l4(lambda)[saga-create-ticket] in saga

    service ddb(dynamodb)[DynamoDB] in data
    
    service sqs(sqs)[SQS] in worker
    service w1(eks)[ticket-worker] in worker
    service w2(eks)[notification-service] in worker
    service s3(s3)[Amazon S3] in worker
    service sns(sns)[Amazon SNS] in worker

    %% Connections
    web:R --> L:gateway
    gateway:R --> L:sf
    
    sf:B --> T:l1
    sf:B --> T:l2
    sf:B --> T:l3
    sf:B --> T:l4
    
    l1:B --> T:ddb
    l3:B --> T:ddb
    l4:B --> T:ddb
    
    l4:R --> L:sqs
    sqs:R --> L:w1
    sqs:R --> L:w2
    
    w1:R --> L:s3
    w2:R --> L:sns
```

> **Nota AWS18**: El equivalente de este esquema visualizado nativamente con arquitectura Beta usa íconos oficiales del set "AWS18", donde los rectángulos usan de forma estricta los logotipos técnicos correspondientes de AWS.
