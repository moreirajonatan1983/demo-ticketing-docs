from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import SQS, Eventbridge, StepFunctions
from diagrams.aws.database import DynamodbTable
from diagrams.aws.storage import S3
from diagrams.aws.compute import Fargate
from diagrams.onprem.client import Users

# --- Diagrama 2: SAGA Checkout Flow ---
with Diagram("SAGA Checkout & Compensation Flow (us-east-1)", show=False, filename="assets/diagrams/aws_saga_flow", direction="LR"):

    user = Users("Client\nWeb / Mobile")

    with Cluster("AWS Region: us-east-1"):
        with Cluster("API Gateway"):
            checkout_entry = Lambda("Checkout API\nLambda")

        with Cluster("SAGA Orchestration"):
            step_fn = StepFunctions("Step Functions\nSAGA Orchestrator")

        with Cluster("AZ-A / Transactional Logic"):
            seats = Lambda("Seats Engine\nOptimistic Lock")
            payment = Lambda("Payment Bridge\nLambda")
            tickets = Lambda("Tickets Lambda\nMetadata Store")
            
            db_seats = DynamodbTable("DynamoDB\nSeats Table")
            db_tickets = DynamodbTable("DynamoDB\nTickets Table")

        with Cluster("AZ-A / AZ-B — Async Processing"):
            eb = Eventbridge("EventBridge\nBus")
            sqs = SQS("SQS:\nTicketPurchased Queue")
            
            with Cluster("ECS Fargate"):
                pdf_worker = Fargate("PDF Worker\nJava/Spring Boot")
                notif = Fargate("Notification Svc\nJava/Spring Boot")
            
            s3_dest = S3("S3 Bucket\nTickets PDF")

    user >> checkout_entry >> step_fn

    step_fn >> Edge(label="1. Reserve Seat") >> seats >> db_seats
    step_fn >> Edge(label="2. Auth Payment") >> payment
    payment >> Edge(label="3. Generate Ticket", color="green") >> tickets >> db_tickets
    payment >> Edge(label="COMPENSATE: Release", color="red", style="dashed") >> seats

    tickets >> Edge(label="4. Publish Event") >> eb >> sqs
    sqs >> pdf_worker >> s3_dest
    sqs >> notif
