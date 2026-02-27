# Guía de Configuración para Desarrolladores (Local Setup)

Este documento detalla los pasos exactos y las herramientas requeridas para que cualquier miembro del equipo pueda compilar, probar y emular toda la Ticketera Cloud en su entorno de desarrollo local, garantizando un índice de gastos de `$0.00` en AWS durante las fases de validación.

## 1. Prerrequisitos y Herramientas Base

Deberás tener instalado en tu estación de trabajo (macOS, Linux o Windows WSL2) lo siguiente:

1.  **Docker Desktop / OrbStack**: Motor de contenedores (Requisito indispensable para SAM y Minikube).
2.  **AWS CLI**: Configurado con un perfil local, aunque apunte a credenciales temporales o dummy para pruebas de Mock.
3.  **AWS SAM CLI**: La herramienta oficial para emular y compilar `AWS Lambda` localmente, y levantar APIs enteras de forma local con Docker.
4.  **Minikube & `kubectl`**: El simulador de clúster Kubernetes local para levantar el Worker de reportes/compresión.
5.  **Golang 1.21+ o Node.js 20+** (Revisar repositorio local específico): Dependiendo de sobre qué runtime iteraremos los microservicios core.

---

## 2. Levantando el Entorno Serverless (Ticketera Core)

El repositorio `demo-ticketing-core` aloja la arquitectura AWS. Se utiliza **SAM Local** para levantar la API transaccional en el puerto `3000`.

1.  Clonar el repositorio y entrar: `cd demo-ticketing-core`.
2.  Ejecutar el build del motor SAM:
    ```bash
    sam build
    ```
3.  *Opcional*: Si tu código de Lambda apunta a base de datos, levanta un contenedor de DynamoDB Local en paralelo:
    ```bash
    docker run -p 8000:8000 amazon/dynamodb-local
    ```
4.  Levantar el API Gateway localmente (Conectado caliente al código):
    ```bash
    sam local start-api --port 3000 --debug
    ```
5.  ¡Listo! Puedes hacer peticiones REST locales contra `http://localhost:3000` y SAM creará contenedores efímeros de Docker para emular la Lambda exactamente igual a AWS.

---

## 3. Levantando el Worker Asíncrono (Kubernetes / Minikube)

El proceso pesado (e.g. compilar mil PDFs de entradas tras un Sold-Out) no corre en Lambda. Corre en nuestro clúster local para probar el patrón de consumidor SQS/KEDA.

1.  Iniciar el clúster local limpio (consume aprox. 2GB de RAM local):
    ```bash
    minikube start --driver=docker
    ```
2.  (Opcional) Instalar KEDA (Kubernetes Event-driven Autoscaling) de forma local usando Helm si deseamos probar auto-escalado agresivo leyendo del SQS real de AWS:
    ```bash
    helm repo add kedacore https://kedacore.github.io/charts
    helm install keda kedacore/keda --namespace keda --create-namespace
    ```
3.  Aplicar el Deployment y ConfigMap del Worker de Tickets localizado en la carpeta `/k8s` del Core:
    ```bash
    kubectl apply -f k8s/worker-deployment.yaml
    ```
4.  Revisar que el Pod del trabajador levantó exitosamente buscando mensajes en SQS:
    ```bash
    kubectl get pods
    kubectl logs -f -l app=ticket-worker
    ```

---

## 4. Estándares de Emulación de AWS Cognito (Auth)

Para la capa de autenticación: 
Dado que **Amazon Cognito** no cuenta con una imagen de Docker ("Local") 100% oficial ni fidedigna de AWS probada para Pooles de Usuarios, el equipo adoptará alguna de estas dos posturas documentadas en el equipo de DevOps:
- A) Usar cuentas efímeras gratuitas **Dev IAM Profiles** en `demo-ticketing-auth` para que el Localhost autentique contra un Cognito en la Nube real durante las pruebas (Recomendado, dada su capa gratuita).
- B) Ocultar Cognito localmente detrás de un **Wrapper / Mock JWT** autogenerado en RSA256 dentro de la Arquitectura Hexagonal de los test unitarios.
