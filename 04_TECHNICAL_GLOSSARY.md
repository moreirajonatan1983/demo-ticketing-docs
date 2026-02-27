# Diccionario Técnico y Glosario del Proyecto

Para mantener coherencia transversal en la arquitectura y facilitar la revisión del código a desarrolladores y evaluadores técnicos, este documento establece el vocabulario oficial utilizado en la plataforma "Ticketera Cloud".

## 1. Arquitectura y Patrones (Traducciones y Conceptos)

*   **SAGA Pattern (Patrón Saga)**: Secuencia coordinada de sub-transacciones. Si un paso de la secuencia transaccional falla, se ejecutan "Transacciones Compensatorias" (Compensating Transactions) para deshacer un impacto previo (e.g. liberar el asiento previamente bloqueado).
*   **Circuit Breaker (Cortocircuito)**: Patrón de diseño que previene llamadas consecutivas a un servicio remoto o base de datos que está reportando fallos recurrentes, desviando el tráfico (o respondiendo error rápido) temporalmente ("Circuito Abierto").
*   **Pub/Sub (Publicador/Suscriptor)**: Patrón de mensajería asíncrona donde los envíos de mensajes ("Publishers") publican o emiten eventos hacia un "Topic" o "Bus", sin saber qué entidades van a terminar consumiendo ("Subscribers").
*   **CQRS (Command-Query Responsibility Segregation)**: Patrón donde las clases, funciones o tablas exclusivas que leen datos (*Queries*) se encuentran rígidamente separadas de aquellas enfocadas en mutar (escribir, cambiar, borrar) datos (*Commands*).
*   **BFF (Backend For Frontend)**: Patrón de diseño donde cada cliente específico (Ej. Móvil vs Web) posee su propia capa/servidor de API Gateway a medida en el backend. Esto permite retornar al celular solo los bytes que realmente necesita, agregando múltiples llamadas complejas del Core en una sola petición simplificada para el front-end.
*   **Hexagonal Architecture (Ports and Adapters)**: Arquitectura de software en donde el Dominio o Regla de Negocio es el centro (Hexágono) completamente limpio e independiente, mientras el mundo exterior (APIs, Bases de Datos) se maneja puramente inyectando Adaptadores mediante Puertos (Interfaces).

## 2. Conceptos AWS / Cloud-Native

*   **Serverless (Sin Servidor)**: Paradigma de la ejecución en nube donde el desarrollador construye el código nativo sin preocuparse en absoluto por provisionar o mantener/parchear el sistema subyacente del sistema operativo (Lambdas).
*   **Cold Start (Arranque en Frío)**: Latencia/Demora inherente y ocasional de **AWS Lambda** causada por el entorno de AWS descargando el código e iniciando un nuevo contenedor base al recibir una petición repentina tras inactividad o auto-escalado veloz. 
*   **Capacity Unit (WCU / RCU)**: Cuota de consumo en **DynamoDB**. Mide la cantidad de Lecturas (Read) o Escrituras (Write) atómicas generadas por segundo bajo determinado peso en bytes.
*   **Blast Radius (Radio de Explosión)**: Concepto vital en arquitecturas "Multi-Account". Representa cuál es el límite físico y lógico de daño o peligro que causaría la filtración de credenciales, un bug en un script borrador, o ataques malintencionados. Separar recursos usando **AWS Organizations** reduce este radio considerablemente de una cuenta comprometida a otra.
*   **AWS SAM (Serverless Application Model)**: Extensión open-source de IaC montada sobre CloudFormation, optimizada con una CLI local dedicada a compilar, emular y testear servicios en AWS (ej. Lambdas/APIs).

## 3. Dominio de Cargas Altas (Ticketera)

*   **Virtual Waiting Room (Sala de Espera Virtual)**: Un componente Cloud (usualmente alojado en el Edge/CDN o vía servicios ultra veloces como AWS ElastiCache) que se activa automáticamente al detectar una avalancha inminente (Flash Crowd) y rutea el exceso de tráfico a una fila virtual cronometrada. Su objetivo final es resguardar la disponibilidad de la base de datos principal (`Zero Downtime`).
*   **Flash Crowd / Flash Sale (Avalancha)**: Situación recurrente y perjudicial donde un servicio digital que rutinariamente tiene tráfico bajo se ve inundado en segundos (Miles/Millones de personas) causando Cuellos de Botella (Bottlenecking) o parálisis debido al lanzamiento de un producto codiciado de stock limitado.
*   **Throttling (Aceleración/Restricción de Tráfico)**: El acto del `API Gateway` de rechazar peticiones adicionales de un usuario excedido, devolviendo comúnmente una respuesta HTTP `429 Too Many Requests`.
*   **Optimistic Locking (Bloqueo Optimista)**: Técnica de base de datos para prevenir colisiones cuando mil personas quieren escribir (comprar) al mismo objeto (ej. Asiento B4). DynamoDB lo resuelve eximiendo que se haga un *Update* sin antes comprobar si una "Versión" del registro es coincidente con la leída.
*   **Dead Letter Queue / DLQ (Cola de Mensajes Muertos)**: Un almacén secundario de SQS / EventBridge que aloja todo aquel payload, mail o PDF cuya generación/envío falló irremediablemente más de N veces. Funciona como evidencia vital de "Retry exhausto" para revisión de negocio posterior.
