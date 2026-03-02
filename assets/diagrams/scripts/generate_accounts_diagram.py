from diagrams import Diagram, Cluster, Edge
from diagrams.aws.management import Organizations, Cloudtrail, OrganizationsAccount
from diagrams.aws.security import Cognito, IAM
from diagrams.aws.compute import Lambda, Fargate
from diagrams.aws.network import APIGateway
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import StepFunctions
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import SNS
from diagrams.aws.storage import S3

with Diagram("AWS Organizations — Topología Multi-Account (9 cuentas)", show=False, filename="assets/diagrams/aws_multi_account_topology", direction="TB"):
    
    root = Organizations("demo-ticketing\n-management\n(Governance / Root)")

    with Cluster("OU: demo-ticketing"):
        with Cluster("Operations"):
            ops_stage = S3("demo-ticketing\n-operations-stage\ntfstate S3 + ECR")
            ops_prod = S3("demo-ticketing\n-operations-prod\ntfstate S3 + ECR")

        with Cluster("Auth"):
            with Cluster("Stage"):
                auth_s_cog = Cognito("Cognito\nUser Pool STAGE")
                auth_s_iam = IAM("IAM Roles\nSTAGE")
                auth_s_lam = Lambda("Auth Lambdas\nSTAGE")

            with Cluster("Prod"):
                auth_p_cog = Cognito("Cognito\nUser Pool PROD")
                auth_p_iam = IAM("IAM Roles\ PROD")
                auth_p_lam = Lambda("Auth Lambdas\nPROD")

        with Cluster("Workloads"):
            with Cluster("demo-ticketing-stage"):
                apigw_s = APIGateway("API Gateway\nSTAGE")
                fargate_s = Fargate("ECS Fargate\nWorkers STAGE")
                sfn_s = StepFunctions("Step Functions\nSTAGE")
                ddb_s = Dynamodb("DynamoDB\nSTAGE")
                
                apigw_s >> fargate_s
                apigw_s >> sfn_s
                sfn_s >> ddb_s
                fargate_s >> ddb_s

            with Cluster("demo-ticketing-prod"):
                apigw_p = APIGateway("API Gateway\nPROD")
                fargate_p = Fargate("ECS Fargate\nWorkers PROD")
                sfn_p = StepFunctions("Step Functions\nPROD")
                ddb_p = Dynamodb("DynamoDB\nPROD")

                apigw_p >> fargate_p
                apigw_p >> sfn_p
                sfn_p >> ddb_p
                fargate_p >> ddb_p

        with Cluster("Monitoring"):
            with Cluster("demo-ticketing-monitoring-stage"):
                cw_s = Cloudwatch("CloudWatch\nSTAGE")
                ct_s = Cloudtrail("CloudTrail\nSTAGE")
                sns_s = SNS("Alertas SNS\nSTAGE")
                cw_s >> sns_s

            with Cluster("demo-ticketing-monitoring-prod"):
                cw_p = Cloudwatch("CloudWatch\nPROD")
                ct_p = Cloudtrail("CloudTrail\nPROD")
                sns_p = SNS("Alertas SNS\nPROD")
                cw_p >> sns_p

    # Flow connections
    root >> ops_stage
    root >> ops_prod
    root >> auth_s_cog
    root >> auth_p_cog
    root >> apigw_s
    root >> apigw_p
    root >> cw_s
    root >> cw_p

    ops_stage - Edge(color="orange", style="dotted", label="tfstate\nGitHub Actions") >> apigw_s
    ops_prod - Edge(color="orange", style="dotted", label="tfstate\nGitHub Actions") >> apigw_p

    auth_s_lam - Edge(color="gray", label="JWT Validation") >> apigw_s
    auth_p_lam - Edge(color="gray", label="JWT Validation") >> apigw_p

    apigw_s - Edge(color="blue", style="dashed", label="Logs/Metrics") >> cw_s
    apigw_p - Edge(color="blue", style="dashed", label="Logs/Metrics") >> cw_p
    auth_s_lam - Edge(color="blue", style="dashed", label="CloudTrail") >> ct_s
    auth_p_lam - Edge(color="blue", style="dashed", label="CloudTrail") >> ct_p
