from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.security import Cognito, WAF, SecretsManager
from diagrams.aws.network import CloudFront
from diagrams.onprem.client import Users

# --- Diagrama 3: Auth & Security Flow ---
with Diagram("Auth & Security Flow (us-east-1)", show=False, filename="assets/diagrams/aws_auth_flow", direction="LR"):

    user = Users("Client\nWeb / Mobile")

    with Cluster("AWS Region: us-east-1\n— Edge & Security Layer —"):
        waf = WAF("AWS WAF\nOWASP Rules\n Rate Limit IP")
        cf = CloudFront("CloudFront\nEdge Locations")

    with Cluster("us-east-1 — Auth Services"):
        api_gw = APIGateway("API Gateway\nCentral Entry Point\n(us-east-1)")

        with Cluster("demo-ticketing-auth-backend"):
            with Cluster("Hexagonal Go Lambdas"):
                authorizer = Lambda("Custom Authorizer\n(Validate JWT)")
                gen_token = Lambda("Auth Generator\n(Issue JWT)")
            
            secrets = SecretsManager("Secrets Manager\nJWT_SECRET")
            
        cognito = Cognito("Amazon Cognito\nUser Pool\n(Future: Production SSO)")

    with Cluster("Protected Resources"):
        core_apis = Lambda("Core API Lambdas\n(Events, Seats, Checkout)")

    # Flow: Login
    user >> Edge(label="1. POST /auth\n{email, password}") >> waf
    waf >> cf >> api_gw
    
    api_gw >> Edge(label="2. Route /auth") >> gen_token
    gen_token >> Edge(label="3. Read JWT_SECRET", style="dashed") >> secrets
    gen_token >> Edge(label="4. Return JWT", color="green") >> user

    # Flow: Authorized request
    user >> Edge(label="5. Request + Bearer Token") >> waf
    waf >> api_gw
    api_gw >> Edge(label="6. Invoke Authorizer", style="dashed") >> authorizer
    authorizer >> Edge(label="7. Validate JWT", style="dashed") >> secrets
    authorizer >> Edge(label="8. Allow/Deny Policy", color="green") >> api_gw
    api_gw >> Edge(label="9. Forward request (if Allowed)") >> core_apis

    # Cognito note
    cognito >> Edge(label="Future: OIDC SSO\nActive Directory", style="dotted", color="gray") >> api_gw
