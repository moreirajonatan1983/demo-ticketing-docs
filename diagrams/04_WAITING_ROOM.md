# Arquitectura de la Sala de Espera Virtual (Virtual Waiting Room)

El componente más crítico de un sistema de "Flash Sales" (Venta Masiva) es evitar sobrecargar el Core de la aplicación. Para lograrlo, la arquitectura incorpora una **Sala de Espera Virtual**.

El objetivo primario de la sala de espera no es solo proteger las bases de datos (Throttling), sino también entregar una experiencia de usuario transparente, indicándole cuántas personas tiene adelante y un tiempo estimado de espera sin que sienta que la página "se colgó".

## 1. Diseño Arquitectónico (Implementación Cloud-Native)

Se opta por un diseño apoyado fuertemente en **Caché y Mensajería Rápida (ElastiCache - Redis / SQS)**, donde la fila se administra fuera de los componentes transaccionales lentos.

```mermaid
architecture-beta
    group client(cloud)[Front End]
    group k8s(cloud)[Kubernetes EKS]
    group data(cloud)[Cache Storage]

    service web(internet)[Client App] in client
    
    service wr(eks)[waiting-room-service] in k8s
    service p(prometheus)[Prometheus] in k8s
    
    service r(elasticache)[Redis Cache] in data

    web:R --> L:wr
    wr:R --> L:r
    p:B --> T:wr
```

## 2. Flujo Explicado (Paso a Paso)

1. **Intento de Acceso al Evento**: Cuando el usuario hace click en comprar, el frontend lo redirige a la ruta `/waiting-room`.
2. **Ingreso a la Fila (Queueing)**: El componente llama a `POST /waiting-room/join`. El servicio Java utiliza **Redis Sorted Sets (ZADD)** usando el `timestamp` como puntuación (score) para garantizar el orden de llegada (FIFO).
3. **Polling Visual en el Front-End**: React inicia un polling cada 3 segundos a `GET /waiting-room/status/{tokenId}`. El servicio calcula la posición usando **ZRANK** y estima el tiempo de espera (ETA) basado en el `admissionRate`.
4. **Liberación Controlada (Admission Tick)**: Un proceso `@Scheduled` en el servicio Java "vacía" la cola cada segundo admitiendo a los primeros `N` usuarios (configurable). Esto protege al resto de los microservicios de picos de carga repentinos.
5. **Autorización y Pase Libre**: Cuando el estado del token cambia a `ADMITTED` en Redis, el siguiente polling del frontend recibe `canProceed: true`. La UI redirige automáticamente al flujo de **Checkout (SAGA)**.
