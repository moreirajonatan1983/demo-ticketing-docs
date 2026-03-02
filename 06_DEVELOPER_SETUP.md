# Guía de Configuración para Desarrolladores (Local Setup)

Este documento detalla los pasos exactos y las herramientas requeridas para que cualquier miembro del equipo pueda compilar, probar y emular toda la Ticketera Cloud en su entorno de desarrollo local, garantizando un índice de gastos de `$0.00` en AWS durante las fases de validación.

## 1. Prerrequisitos y Herramientas Base

Deberás tener instalado en tu estación de trabajo (macOS, Linux o Windows WSL2) lo siguiente:

1.  **Docker Desktop / OrbStack**: Motor de contenedores (Requisito indispensable).
2.  **AWS CLI / AWS CLI Local (`awslocal`)**: Herramientas para interactuar con AWS y LocalStack.
3.  **AWS SAM CLI**: Para emular `AWS Lambda` localmente.
4.  **LocalStack**: Emulación de SQS, S3, DynamoDB y Step Functions localmente.
5.  **Minikube & `kubectl` / `helm`**: Cluster local para los servicios Java y KEDA.
6.  **Golang 1.21+, Node.js 20+, Java 21 y Maven**: Lenguajes y gestores de dependencias necesarios.

---

## 2. Levantando el Entorno Serverless (Ticketera Core)

El repositorio `demo-ticketing-backend` aloja la arquitectura AWS. Se utiliza **SAM Local** para levantar la API transaccional en el puerto `3000`.

1.  **Iniciar LocalStack**:
    ```bash
    docker run -d -p 4566:4566 -p 4510-4559:4510-4559 localstack/localstack
    ```
2.  **Configurar Infraestructura y SAGA**:
    Ejecutar el script que crea colas SQS, buckets S3, tablas DynamoDB y la **State Machine** de Step Functions:
    ```bash
    cd demo-ticketing-backend
    ./scripts/setup_saga.sh
    ```
3.  **Levantar Lambdas con SAM**:
    ```bash
    sam build && sam local start-api --port 3000
    ```

---

## 3. Levantando el Worker Asíncrono (Kubernetes / Minikube)

El proceso pesado (e.g. compilar mil PDFs de entradas tras un Sold-Out) no corre en Lambda. Corre en nuestro clúster local para probar el patrón de consumidor SQS/KEDA.

1.  **Iniciar Minikube**:
    ```bash
    minikube start --driver=docker
    ```
2.  **Habilitar Ingress y KEDA**:
    ```bash
    minikube addons enable ingress
    helm repo add kedacore https://kedacore.github.io/charts
    helm install keda kedacore/keda --namespace keda --create-namespace
    ```
3.  **Compilar y Desplegar Servicios Java**:
    Para cada servicio (`waiting-room-service`, `ticket-worker`, `notification-service`):
    ```bash
    cd demo-ticketing-services-backend/services/[service-name]
    mvn clean package -DskipTests
    # Construir imagen en el daemon de minikube
    eval $(minikube docker-env)
    docker build -t [service-name]:latest .
    # Aplicar manifiestos
    kubectl apply -f k8s/
    ```
4.  **Verificar Autoscale (KEDA)**:
    ```bash
    kubectl get pods -n ticketera
    kubectl logs -f -l app=ticket-worker -n ticketera
    ```

### 3.1. Monitoreo del Clúster (Prometheus / Grafana)
Todas las aplicaciones Java inyectan sus métricas a través de sus endpoints `/actuator/prometheus`.
Para visualizar la telemetría métrica en tiempo real y el estado de los workers, debes invocar el stack the Prometheus desde tu cluster Minikube:
1.  **Ejecutar el Port-Forward al servidor de Dashboards (Grafana)**:
    ```bash
    kubectl port-forward svc/prometheus-grafana 3001:80 -n monitoring
    ```
    Y accede al navegador apuntando a `http://localhost:3001` (User: `admin`). La base de datos de telemetría inyectada se actualiza cada 5s.

---

## 4. Estándares de Emulación de AWS Cognito (Auth)

Para la capa de autenticación: 
Dado que **Amazon Cognito** no cuenta con una imagen de Docker ("Local") 100% oficial ni fidedigna de AWS probada para Pooles de Usuarios, el equipo adoptará alguna de estas dos posturas documentadas en el equipo de DevOps:
- A) Usar cuentas efímeras gratuitas **Dev IAM Profiles** en `demo-ticketing-auth` para que el Localhost autentique contra un Cognito en la Nube real durante las pruebas (Recomendado, dada su capa gratuita).
- B) Ocultar Cognito localmente detrás de un **Wrapper / Mock JWT** autogenerado en RSA256 dentro de la Arquitectura Hexagonal de los test unitarios.

---

## 5. Scripts de Orquestación Local (All-in-One)

Para facilitar la vida del desarrollador y no tener que levantar múltiples terminales para el Backend y el Web Frontend simultáneamente, el repositorio base incluye utilitarios de automatización.

Deberás utilizar los scripts ubicados en el directorio `demo-ticketing-backend/scripts/` para levantar armónicamente todo el proyecto (API + SPA React):

- `./scripts/start_all.sh`: Compila SAM, levanta el API Gateway local, y lanza el servidor de desarrollo de `demo-ticketing-web` (Vite) en background o multiplexado, atando los logs a una sola pantalla.
- `./scripts/stop_all.sh`: Mata los procesos huérfanos de SAM local, contenedores Docker efímeros de DynamoDB y frena el servidor Vite de React de forma limpia.
- `./scripts/restart_all.sh`: Fuerza una recompilación dura (hard-refresh) de los binarios Lambda y reinicia todo el stack frontal.
