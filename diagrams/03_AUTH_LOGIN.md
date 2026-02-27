# Diagrama de Autenticación Centralizada y Seguridad (Login)

La topología de seguridad se encuentra gobernada por **Amazon Cognito** (dentro del repositorio e infraestructura `demo-ticketing-auth`).

**Sobre JWT:** Amazon Cognito es 100% compatible con los estándares de OpenID Connect (OIDC) y OAuth2. Esto significa que **sí, Cognito utiliza directamente tokens JWT**. Cuando un usuario se autentica de forna exitosa, Cognito emite:
1.  **Id_Token**: Un JSON Web Token (JWT) que contiene claims sobre la identidad directa del usuario (Email, Nombre, ID Subjetivo de usuario).
2.  **Access_Token**: JWT que dicta "Qué permisos tiene" a nivel Oauth. Fundamental porque el `Amazon API Gateway` del Core puede validar nativa e instantáneamente si la firma asimétrica de este token corresponde y el rol inyectado está activo, sin consultar a Cognito.
3.  **Refresh_Token**: Un token ofuscado que emite nuevos Access Tokens a las 24hs automáticamente, manteniendo al usuario logueado en su teléfono pero bloqueándolo si el admin decide cerrarle la cuenta en el backend.

```mermaid
sequenceDiagram
    participant WebApp as Client Web SPA
    participant Cognito as Amazon Cognito (Auth Account)
    participant APIGW as API Gateway (Core Account)
    participant Lambda as Lambda Function

    %% Proceso de Autenticacion/Login FrontEnd %%
    Note over WebApp,Cognito: Flujo SRP (Secure Remote Password) de Cognito
    WebApp->>Cognito: POST /login (username, auth hash password)
    Cognito-->>WebApp: Retorna Tokens JWT (IdToken, AccessToken, RefreshToken)

    %% Interacción protegida en el backend %%
    Note over WebApp,Lambda: Usuario solicita información privada transaccional
    WebApp->>APIGW: GET /api/v1/user/orders (Header: Authorization Bearer [AccessToken])
    
    APIGW->>APIGW: 1. Valida algorítmo local de la firma (RS256) contra la JWKS OIDC.
    APIGW->>APIGW: 2. Determina si el JWT expiró.
    
    alt Token Inválido o Expirado
        APIGW-->>WebApp: 401 Unauthorized (Sin despertar a Lambda - Ahorro de Costos)
    else JWT Totalmente Valido
        APIGW->>Lambda: Forward Request inyectando los claims del usuario desde el JWT (ej: `sub` / UUID del usuario)
        Lambda-->>APIGW: Responde datos privados (Histórico de Tickets DB)
        APIGW-->>WebApp: 200 OK
    end
```
