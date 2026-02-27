# Diagrama C4 (Contexto)

Este diagrama C4 de Nivel 1 (Context) expone el límite del sistema de toda la Ticketera Cloud en relación a sus actores y dependencias externas. Es un vistazo a "20,000 pies de altura" para entender el alcance final del proyecto desde una perspectiva de dominio de software.

```mermaid
%%{init: {'theme': 'default'}}%%
C4Context
    title Diagrama de Contexto de Sistema (C4) - Ticketera Cloud

    Person(user, "Comprador de Ticket", "Usuario final que busca catálogos de eventos, reserva asientos y adquiere las entradas a través de la WebApp y canales móviles.")
    Person(admin, "Productora/Administrador", "Empleados u organizadores del evento que revisan las métricas y recaban reportes financieros en formato CSV de las ventas.")
    
    System(ticketera, "Ticketera Cloud System", "SaaS Core (Nuestra Aplicación). Gestiona el catálogo, concurrencia, autorizaciones, compras y emisiones de PDF masivos.")
    
    System_Ext(gateway_pago, "Pasarela de Pagos (Stripe/MercadoPago)", "Procesa y verifica la transaccionalidad de tarjetas de crédito o débito a los compradores.")
    System_Ext(cognito_auth, "Identity Provider (demo-ticketing-auth)", "Servicio en cuenta AWS dedicada a delegar la identidad de compradores y la capa de administración usando credenciales.")
    System_Ext(notificaciones, "Push Notification & Email Service", "Medio por el que los clientes se enteran de novedades e imprevistos instantáneos o envíos transaccionales (AWS SNS / SES).")
    
    Rel(user, ticketera, "Busca eventos, se loguea y compra entradas", "HTTPS")
    Rel(user, cognito_auth, "Se registra, valida identidad", "HTTPS / OpenID Connect")
    
    Rel(admin, ticketera, "Extrae reportes financieros batchs generados por el worker en Minikube", "HTTPS")
    Rel(admin, cognito_auth, "Ingresa al pool de administradores", "HTTPS / SAML")
    
    Rel(ticketera, gateway_pago, "Deduce fondos monetarios y valida cobro", "Rest API secured")
    Rel(ticketera, notificaciones, "Dispara avisos a los teléfonos moviles y reenvía correos de confirmación")
    Rel(ticketera, cognito_auth, "Valida el JWT firmado de cada API Request de los usuarios entrantes al Gateway")
```
