from diagrams import Diagram, Cluster, Edge
from diagrams.aws.management import Organizations, Cloudwatch, Cloudtrail
from diagrams.aws.integration import SNS
from diagrams.aws.network import Route53
from diagrams.aws.security import Cognito, IAM
from diagrams.aws.compute import Lambda, Fargate
from diagrams.aws.database import DynamodbTable
from diagrams.aws.storage import S3
from diagrams.aws.devtools import Codecommit  # ECR
from diagrams.aws.network import APIGateway
from diagrams.aws.integration import StepFunctions, Eventbridge

with Diagram(
    "AWS Organizations — Multi-Account Topology (9 cuentas)",
    show=False,
    filename="assets/diagrams/aws_multi_account_topology",
    direction="TB",
    graph_attr={"fontsize": "14", "pad": "0.5"}
):
    root = Organizations("demo-ticketing\n-management\n(Governance / Root)")

    with Cluster("OU: Operations"):
        ops_stage = S3("demo-ticketing\n-operations-stage\ntfstate S3 + ECR")
        ops_prod  = S3("demo-ticketing\n-operations-prod\ntfstate S3 + ECR")

    with Cluster("OU: Auth"):
        with Cluster("Stage"):
            auth_stage_cog = Cognito("Cognito\nUser Pool STAGE")
            auth_stage_iam = IAM("IAM Roles\nSTAGE")
            auth_stage_lmb = Lambda("Auth Lambdas\nSTAGE")
        with Cluster("Prod"):
            auth_prod_cog  = Cognito("Cognito\nUser Pool PROD")
            auth_prod_iam  = IAM("IAM Roles\nPROD")
            auth_prod_lmb  = Lambda("Auth Lambdas\nPROD")

    with Cluster("OU: Workloads"):
        with Cluster("demo-ticketing-stage"):
            apigw_stage = APIGateway("API Gateway\nSTAGE")
            dynamo_stage = DynamodbTable("DynamoDB\nSTAGE")
            fargate_stage = Fargate("ECS Fargate\nWorkers STAGE")
            sf_stage     = StepFunctions("Step Functions\nSTAGE")
        with Cluster("demo-ticketing-prod"):
            apigw_prod  = APIGateway("API Gateway\nPROD")
            dynamo_prod  = DynamodbTable("DynamoDB\nPROD")
            fargate_prod = Fargate("ECS Fargate\nWorkers PROD")
            sf_prod      = StepFunctions("Step Functions\nPROD")

    with Cluster("OU: Monitoring"):
        with Cluster("demo-ticketing-monitoring-stage"):
            cw_stage     = Cloudwatch("CloudWatch\nSTAGE")
            ct_stage     = Cloudtrail("CloudTrail\nSTAGE")
            sns_stage    = SNS("Alertas SNS\nSTAGE")
        with Cluster("demo-ticketing-monitoring-prod"):
            cw_prod      = Cloudwatch("CloudWatch\nPROD")
            ct_prod      = Cloudtrail("CloudTrail\nPROD")
            sns_prod     = SNS("Alertas SNS\nPROD")

    # Root → OUs
    root >> Edge(style="dashed") >> ops_stage
    root >> Edge(style="dashed") >> ops_prod
    root >> Edge(style="dashed") >> auth_stage_cog
    root >> Edge(style="dashed") >> auth_prod_cog
    root >> Edge(style="dashed") >> apigw_stage
    root >> Edge(style="dashed") >> apigw_prod
    root >> Edge(style="dashed") >> cw_stage
    root >> Edge(style="dashed") >> cw_prod

    # Operations: GitHub Actions asume rol → tfstate
    ops_stage >> Edge(label="tfstate\nGitHub Actions", style="dotted", color="orange") >> apigw_stage
    ops_prod  >> Edge(label="tfstate\nGitHub Actions", style="dotted", color="orange") >> apigw_prod

    # Auth → Workloads
    auth_stage_lmb >> Edge(label="JWT Validation") >> apigw_stage
    auth_prod_lmb  >> Edge(label="JWT Validation") >> apigw_prod

    # Workload internals
    apigw_stage >> sf_stage >> dynamo_stage
    apigw_stage >> fargate_stage

    apigw_prod >> sf_prod >> dynamo_prod
    apigw_prod >> fargate_prod

    # Workloads → Monitoring (cross-account logs)
    apigw_stage >> Edge(label="Logs/Metrics", color="blue", style="dashed") >> cw_stage
    apigw_prod  >> Edge(label="Logs/Metrics", color="blue", style="dashed") >> cw_prod

    auth_stage_lmb >> Edge(label="CloudTrail", color="blue", style="dashed") >> ct_stage
    auth_prod_lmb  >> Edge(label="CloudTrail", color="blue", style="dashed") >> ct_prod

    cw_stage >> sns_stage
    cw_prod  >> sns_prod
