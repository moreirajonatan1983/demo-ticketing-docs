# Diseño de Pantallas y Experiencia de Usuario (UI/UX)

La plataforma `demo-ticketing` no sólo ostentará una robusta ingeniería backend. Para demostrar un nivel "Enterprise" integral, se especifica la arquitectura y flujos front-end mínimos requeridos de una Web App consumidora (SPA - React/Next.js/Vue) interactuando contra `demo-ticketing-backend` y `demo-ticketing-auth-backend`.

## 1. Patrón Visual General
- **Estética "Premium" Moderno**: Glassmorphism (paneles ligeramente translúcidos), gradientes oscuros o 'Dark Mode' por defecto, tipografía moderna sin serifa (e.g. `Inter`, `Manrope`), y skeleton loaders para indicar procesamiento asíncrono sin bloquear la pantalla al usuario.
- **Responsividad (Mobile-First)**: Dada la inmensa cantidad de ventas móviles en Ticketing, todo el grid (Flexbox/Grid CSS) debe fluir en resoluciones de celular `375px` o superiores.

---

## 2. Mapa de Pantallas (Wireflow Básico)

### 2.1 Pantalla Principal: "Catálogo Flash" (`/events`)
*Punto de entrada general y flujo atado al CQRS (Lectura de catálogos desnormalizados).*
- **Hero Banner**: Carrusel rotativo con eventos destacados o pre-ventas inminentes.
- **Search & Filter Bar**: Barra persistente para debounced-search contra ElasticSearch/Aurora y filtros por categoría (Recitales, Teatro, Deportes).
- **Event Grid**: Tarjetas limpias de los eventos activos informando estado de inventario a simple vista (Disponible, Pocos Tickets o "Sold Out").

### 2.2 Pantalla de Seguridad: "Login & Register Model" (`/auth`)
*Interactúa nativamente contra Cognito a través de SDKs Front-End o Auth APIs.*
- Modal (Popup/Slide-in) unificado para evitar cambiar violentamente de ruta de pantalla.
- Opciones de Social Login (Google) configurado en el User Pool OIDC.
- Formularios fluidos para "Forgot Password" conectados al flujo Cognito SRP nativo.

### 2.3 Sala de Espera Virtual (Queue Room)
*Punto de contención temporal frente a "Flash Sales". Se activa si un evento supera el umbral X de concurrentes.*
- Diseño minimalista para consumir el menor ancho de banda posible.
- Contador regresivo en tiempo real ("Estás en la posición #543 de la fila virtual").
- Alerta al navegador/usuario cuando es su turno emitiendo un sonido y otorgándole una ventana de 3 minutos para pasar al Checkout antes de perder su "bolsa" temporal.

### 2.4 Pantalla Detalle de Evento: "Checkout - Paso 1" (`/events/{event_id}`)
*Punto donde empieza el riesgo de alta concurrencia. Aquí inician el polling del estado real de los asientos bajo la supervisión de la Sala de Espera.*
- Detalles descriptivos del concierto e imágenes inmutables subidas via S3 CDN.
- **Mapa de Asientos o Sectores (Seating Planner)**: Panel de botones interactivos donde localidades temporalmente bloqueadas (por la Lambda SAGA Reservadora de otra persona) se colorean "Gris/Bloqueadas" gracias a WebSockets/Polling corto contra API Gateway.
- Botón principal flotante (Sticky): "Añadir a carrito" con loader asíncrono.

### 2.4 Pantalla de Procesamiento Seguro: "Checkout - Paso 2" (`/checkout/payment`)
*Interactúa con el Nodo 2 del SAGA (Pago).*
- Timer Global: El usuario tiene 05:00 minutos de "Reserva Temporal Fuerte". Si el timer se agota localmente, se dispara limpieza (Rollback en Lambda compensatoria).
- **Formulario Pasarela de Pagos**: UI simulada pidiendo tarjeta, integrada virtualmente de modo de no retener esos datos críticos en base, simplemente pasando tokens al Core o esperando respuesta externa (Circuit Breaker activo aquí).
- **Estado de Carga Asíncrono (Skeleton/Spinner)**: Pantalla intercluya validando la confirmación, manejando posibles estados: "Aprobado", "Rechazado", "Timeout Servidor" (compensación forzosa por saturación). 

### 2.5 Pantalla del Comprador Privada: "Mis Tickets" (`/profile/tickets`)
- Panel de gestión para visualizar eventos pasados y próximos consumiendo el JWT en cada llamada `Bearer [Token]` en el Dashboard API REST.
- Render estático de los Códigos QR por Entrada.
- Opción a un botón "Descargar Entradas en PDF" (Detona en background al Worker en AWS ECS Fargate).

### 2.6 Pantalla Administrativa [Solo Productores]: "Dashboard BI Metrics" (`/admin`)
- Pantalla protegida y ruteada exclusivamente si el Token JWT expuesto posee la propensión (claim) o rol IAM de Administrador (Role-Based Access Control / RBAC).
- Gráficos integrables de facturación diaria extraídos cruzando métricas en batch desde AWS.
- Botones de comandos: "Publicar evento", "Suspender Venta de Ticket" (Detonan SQS o Dynamo).
