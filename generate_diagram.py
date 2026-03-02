from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Fargate, Lambda
from diagrams.aws.network import CloudFront, APIGateway, ALB
from diagrams.aws.database import DynamodbTable, ElasticacheForRedis
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import SQS, Eventbridge, StepFunctions
from diagrams.aws.storage import S3
from diagrams.aws.security import Cognito, WAF, SecretsManager
from diagrams.onprem.client import Users

with Diagram("AWS Ticketera General Architecture (us-east-1)", show=False, filename="assets/diagrams/aws_general_architecture", direction="LR"):

    users = Users("Users\nGlobal")

    with Cluster("AWS Region: us-east-1"):
        
        with Cluster("Edge & Security"):
            waf = WAF("AWS WAF\nWeb App Firewall")
            cf = CloudFront("CloudFront CDN\nEdge Locations")
            
        with Cluster("Availability Zone A & B"):
            
            with Cluster("Frontend Hosting"):
                s3_front = S3("S3 Bucket\nReact SPA")
            
            with Cluster("demo-ticketing-auth-backend"):
                cognito = Cognito("Amazon Cognito\nUser Pool")
                api_gw = APIGateway("API Gateway\nCentral Auth")
                
                with Cluster("Hexagonal Go Lambdas"):
                    auth_gen = Lambda("Auth/Gen Token")
                    auth_authz = Lambda("Auth/Authorizer")

            with Cluster("demo-ticketing-backend\n(Serverless Transactional Core)"):
                events_func = Lambda("Events API")
                checkout_func = Lambda("Checkout API")
                seats_func = Lambda("Seats Engine")
                tickets_func = Lambda("Tickets Engine")
                
                saga_step = StepFunctions("SAGA Orchestrator\nStep Functions")
                
                with Cluster("Databases (NoSQL)"):
                    db_events = DynamodbTable("Events DB")
                    db_seats = DynamodbTable("Seats DB\n(Optimistic Lock)")
                    db_tickets = DynamodbTable("Tickets DB")
                    
                    redis_cache = ElasticacheForRedis("ElastiCache\nRedis Waiting Room")

            with Cluster("demo-ticketing-services-backend\n(Async Workers & Long Processing)"):
                event_bus = Eventbridge("EventBridge\nBus")
                queue_tickets = SQS("TicketPurchased\nQueue")
                
                with Cluster("Amazon ECS Fargate (Serverless Containers)"):
                    fargate_pdf = Fargate("Ticket PDF Worker\n(Java/Spring Boot)")
                    fargate_notif = Fargate("Notification Service\n(Java/Spring Boot)")
                
                s3_docs = S3("S3 Bucket\nPDF Tickets")

    # Routing
    users >> waf >> cf >> s3_front
    users >> waf >> api_gw
    
    # API Gateway routing
    api_gw >> Edge(label="Custom Auth") >> auth_authz
    api_gw >> Edge(label="/auth") >> auth_gen
    api_gw >> Edge(label="/events") >> events_func
    api_gw >> Edge(label="/checkout") >> checkout_func
    
    # Lambda to BD
    events_func >> db_events
    events_func >> redis_cache
    
    checkout_func >> saga_step
    saga_step >> seats_func
    saga_step >> tickets_func
    
    seats_func >> db_seats
    tickets_func >> db_tickets
    
    # Async flow
    saga_step >> event_bus >> queue_tickets >> fargate_pdf
    queue_tickets >> fargate_notif
    
    fargate_pdf >> s3_docs
