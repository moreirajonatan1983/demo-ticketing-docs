from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import Route53, CloudFront, APIGateway
from diagrams.aws.storage import S3
from diagrams.aws.security import WAF, CertificateManager, Cognito
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import SQS
from diagrams.aws.management import Cloudwatch
from diagrams.onprem.client import Users

with Diagram(
    "Route 53 + Multi-Account Strategy (stage / prod)",
    show=False,
    filename="assets/diagrams/aws_route53_dns",
    direction="TB"
):
    user = Users("Client Browser\n/ Mobile App")

    with Cluster("AWS Route 53 (DNS Global)\nHosted Zone: dominioacomprar.com"):
        r53_root = Route53("dominioacomprar.com\n(Apex Record A/ALIAS)")
        r53_www  = Route53("www.dominioacomprar.com\n(CNAME → CloudFront)")
        r53_api_stage = Route53("api.stage.dominioacomprar.com\n(CNAME → APIGW Stage)")
        r53_api_prod  = Route53("api.dominioacomprar.com\n(CNAME → APIGW Prod)")

    # ─── PROD ACCOUNT ─────────────────────────────────────
    with Cluster("AWS Account: PROD  (us-east-1)"):
        with Cluster("Edge"):
            acm_prod = CertificateManager("ACM Certificate\n*.dominioacomprar.com\n(us-east-1 – CloudFront req)")
            waf_prod = WAF("AWS WAF\nOWASP / Rate Limit")
            cf_prod  = CloudFront("CloudFront Distribution\ndominioacomprar.com\nwww.dominioacomprar.com")

        with Cluster("Frontend Hosting"):
            s3_prod = S3("S3 Bucket\nPROD React SPA\n(Static Web Hosting)")

        with Cluster("API Gateway (Custom Domain)"):
            apigw_prod = APIGateway("api.dominioacomprar.com\nAPI Gateway PROD\n(Custom Domain Mapping)")

        with Cluster("Serverless Core"):
            lambda_prod = Lambda("Core APIs\n(Events, Auth, Checkout…)")

    # ─── STAGE ACCOUNT ────────────────────────────────────
    with Cluster("AWS Account: STAGE  (us-east-1)"):
        with Cluster("Edge"):
            acm_stage = CertificateManager("ACM Certificate\n*.stage.dominioacomprar.com\n(us-east-1)")
            waf_stage = WAF("AWS WAF\nOWASP / Rate Limit")
            cf_stage  = CloudFront("CloudFront Distribution\nstage.dominioacomprar.com")

        with Cluster("Frontend Hosting"):
            s3_stage = S3("S3 Bucket\nSTAGE React SPA")

        with Cluster("API Gateway (Custom Domain)"):
            apigw_stage = APIGateway("api.stage.dominioacomprar.com\nAPI Gateway STAGE")

        with Cluster("Serverless Core"):
            lambda_stage = Lambda("Core APIs STAGE\n(Lower capacity)")

    # ─── DNS ROUTING ──────────────────────────────────────
    user >> Edge(label="1. DNS Lookup") >> r53_root
    user >> Edge(label="1b. DNS Lookup") >> r53_www

    # Apex and www → PROD CloudFront
    r53_root >> Edge(label="ALIAS Record") >> cf_prod
    r53_www  >> Edge(label="CNAME → CloudFront") >> cf_prod

    # stage frontend
    user >> Edge(label="stage.domain") >> cf_stage

    # API routing
    r53_api_prod  >> Edge(label="Custom Domain") >> apigw_prod
    r53_api_stage >> Edge(label="Custom Domain") >> apigw_stage

    # PROD flow
    cf_prod  >> waf_prod  >> s3_prod
    cf_prod  >> waf_prod  >> apigw_prod >> lambda_prod
    acm_prod >> Edge(style="dashed") >> cf_prod

    # STAGE flow
    cf_stage >> waf_stage >> s3_stage
    cf_stage >> waf_stage >> apigw_stage >> lambda_stage
    acm_stage >> Edge(style="dashed") >> cf_stage
