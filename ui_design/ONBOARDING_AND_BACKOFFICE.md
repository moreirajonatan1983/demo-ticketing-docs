# Onboarding de Usuarios y Portal Backoffice

Este documento describe la experiencia de registro inicial (Onboarding) para nuevos compradores en la Ticketera, así como las especificaciones funcionales y visuales requeridas para el panel de administración (Backoffice) utilizado por las productoras de eventos.

---

## 1. Flujo de Onboarding del Comprador (B2C)

Dada la naturaleza crítica de alta concurrencia en la venta de entradas ("Flash Sales"), **el proceso de onboarding no debe ser un bloqueador de la conversión**. Debe ser lo más "frictionless" (sin fricción) posible, apalancándose fuertemente en integraciones de identidad.

### Fases del Onboarding:
1. **Punto de Ingreso Integrado**: Al clickear "Comprar Entrada" en un evento, un modal intercepta al usuario no logueado.
2. **Social Sign-On (SSO)**: Opciones predominantes para **"Continuar con Google"** o **"Continuar con Apple"**. Esto interactúa con el sub-sistema de `demo-ticketing-auth-backend` (Amazon Cognito User Pools) creando la cuenta instantáneamente.
3. **Registro Tradicional (Fallback)**: 
   - Captura de Email y Password.
   - **Validación Asíncrona (OTP)**: AWS Cognito dispara automáticamente un email de validación mediante Amazon SES con un PIN numérico de 6 dígitos.
   - Una pantalla OTP intercepta al usuario. Una vez tipeado, la sesión se activa, devolviéndole inmediatamente su `JWT Token`.
4. **"Perfil Completo" Post-Checkout**: Durante las ventas masivas, _sólo_ se pide nombre y correo en la pasarela. Datos demográficos, DNI para seguridad, o preferencias musicales se solicitan amablemente mediante una "Card de Completitud" en el Dashboard del Comprador **después** de su primera compra exitosa.

---

## 2. Plataforma Backoffice (Admin Panel - B2B)

El Backoffice es el centro de control exclusivo para los Administradores del Sistema y las Productoras Musicales/Teatrales. Accesible únicamente mediante Roles IAM (Role-Based Access Control) incrustados en los claims del Token JWT (`custom:role = admin`).

### 2.1 Módulo: Gestión de Catálogo y Eventos
- **Creador de Eventos**: Un wizard (multi-paso) que permite a la productora cargar un evento nuevo.
  - Sube "Flyers" e imágenes directamente a **Amazon S3** vía pre-signed URLs entregadas por el API Gateway.
  - Configura el Inventario Maestro (Zonas, Sectores y Precios) que inicializará las tablas en **DynamoDB**.
  - Define "Horario de Salida a Venta" (Schedule).

### 2.2 Módulo: Monitoreo Flash Crowd (Control Room)
Panel en tiempo real para visualizar un evento que acaba de salir a la venta masiva.
- **Gráficos en Vivo**: Indicadores consumidos de **Amazon CloudWatch Metrics** expuestos en gráficos (Ventas por segundo, Tasa de rechazo/Timeouts).
- **Kill-Switch Manual (Circuit Breaker Administrativo)**: Un botón rojo de "Pausar Venta" que corta intencionalmente el tráfico en el API Gateway para ese concierto particular, útil si detectan reventa bot masiva inusual o si el aforo físico tuvo una baja repentina de clausura exterior.

### 2.3 Módulo: Reportes y Batch (Worker Link)
Dado que consolidar el PDF "Balance Financiero" de un concierto de estadio requiere recorrer cientos de miles de registros:
- El Backoffice tiene una pestaña **"Descargar Reporte de Cierre"**.
- Al presionarlo, el UI simplemente manda un Request (Command) que inyectará un mensaje en la cola **Amazon SQS**.
- El UI muestra un estado de "Procesando Reporte... Le enviaremos un correo".
- Simultáneamente, el Worker asíncrono en Kubernetes (**Minikube** en local) absorbe el SQS message, macera y procesa la data sin apurar a la base DynamoDB de prod, lo consolida en Excel/CSV, sube el reporte final a `S3`, y el Backend dispara un mail de **Amazon SES** la Productora: *"Su Reporte B2B ya está listo para descargar"*.
