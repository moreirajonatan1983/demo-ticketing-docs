# Esquemas de Datos (Data Schemas) 

Para que la plataforma funcione eficientemente a un nivel altamente concurrente (y pueda absorber los picos de ventas), todo el almacenamiento principal es soportado por bases de datos NoSQL, específicamente **Amazon DynamoDB**. 

A continuación se detalla la estructura física de las tablas y objetos esperados por el sistema backend si se desea inyectar o leer información.

## 1. Eventos (`EventsTable`)
Almacena el detalle general y el catálogo público del evento (ej: "Concierto Coldplay"). Es consumido extensivamente por los queries de lectura del Frontend.

- **Hash Key**: `id` (String) - UUID del evento.
- **Campos esperados**:
  - `title` (String): El título a mostrar al público.
  - `date` (String): Fecha principal conmemorativa (ej. "15 Octubre 2026").
  - `venue` (String): Establecimiento y/o ciudad (ej. "Estadio Nacional").
  - `image` (String): Key alfanumérica dentro del bucket S3 de medias (`ticketera-images-local`) o también puede usarse URL externa si actúa como mock.
  - `status` (String): El estado global del evento (`Disponible`, `Ultimos Tickets`, `Sold Out`, `Rechazado`).

## 2. Shows / Fechas y Horarios (`ShowsTable`)
Permite registrar múltiples fechas u horarios para un mismo "Evento".
- **Hash Key**: `event_id` (String) - Referencia directa al ID en `EventsTable`.
- **Campos esperados**:
  - `id` (String): Sub-ID o DateID para identificar la fecha precisa.
  - `date` (String): Fecha específica del evento en esa instancia.
  - `time` (String): La hora en la cual se abren puertas (ej. "21:00 hs").
  - `status` (String): (`available` | `soldout`).

## 3. Entradas, Asientos y Sectores (`EventSeatsTable`)
Es la tabla más críca transaccional (sobre la cual se hacen *Optimistic Locks* y actualizaciones condicionales para reservar inventario).
- **Hash Key**: `event_id` (String) - El UUID principal del evento.
- **Range Key**: `seat_id` (String) - Un identificador único del bloque o butaca (Ej: "A1").
- **Campos esperados**:
  - `row` (String): Fila o sector nominal.
  - `number` (Number): Número lógico del asiento (en tipo `N`).
  - `status` (String): Estado actual del asiento. Soporta transiciones (`available` -> `processing` -> `sold` / `occupied`). El paso `processing` es donde interviene la SAGA de Step Functions para bloquearlo temporalmente (Timeout 10-15 Minutos preventivos de carritos).

## 4. Tickets Generados  (`TicketsTable`)
Tabla destinada a almacenar los boletos nominales tras una compra Exitosa confirmada por todo el Gateway de pago.
- **Hash Key**: `user_id` (String) - El ID del comprador/usuario logueado en la nube de Cognito.
- **Range Key**: `ticket_id` (String) - UUID generado autoincremental/aleatorio para esa transacción del e-ticket.
- **Campos esperados**:
  *Puede extenderse con códigos QR o metadata para accesos remotos.*

## 5. Cuentas de Usuarios (`UsersTable`)
Se utiliza para correlacionar con perfiles extendidos en DB o claims adicionales más allá del token JWT de identidades provisto por Auth (Suele mapear correos de Cognito hacia datos transaccionales extra).
- **Hash Key**: `email` (String) - Correo del comprador.
