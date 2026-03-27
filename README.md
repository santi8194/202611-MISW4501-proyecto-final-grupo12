# 202611-MISW4501-proyecto-final-grupo12


# Infraestructura con Terraform (AWS)

Este proyecto utiliza Terraform para gestionar la infraestructura en AWS de forma automatizada (Infrastructure as Code).
Se implementa un backend remoto en S3 para almacenar el estado de Terraform, permitiendo:

Trabajo en equipo sin conflictos
Persistencia del estado
Versionado de infraestructura

## Backend remoto (S3)

Se creó un bucket en AWS S3 para almacenar el archivo terraform.tfstate.

## Bucket

*terraform-state-grupo12*

El nombre del bucket debe ser único a nivel global en AWS.

Comando: aws s3api create-bucket --bucket terraform-state-grupo12 --region us-east-1 --debug

# Despliegue del Stack: Container Registry (ECR)

Este stack permite la creación de un repositorio en Amazon ECR usando Terraform, incluyendo una política de ciclo de vida para el manejo automático de imágenes.

Se utiliza una arquitectura basada en:

- modules/ → lógica reutilizable (ECR)
- stacks/ → definición del despliegue
- environments/ → configuración por ambiente

## Inicialización

Inicializa Terraform y configura el backend remoto en S3:

terraform -chdir="$PWD\terraform\stacks\container_registry" init -backend-config="$PWD\terraform\environments\dev\container_registry\backend.tfvars"

## Planificación

Muestra los cambios que se van a aplicar en la infraestructura:

terraform -chdir="$PWD\terraform\stacks\container_registry" plan -var-file="$PWD\terraform\environments\dev\container_registry\terraform.tfvars"

## Despliegue

Aplica los cambios y crea los recursos en AWS:

terraform -chdir="$PWD\terraform\stacks\container_registry" apply -var-file="$PWD\terraform\environments\dev\container_registry\terraform.tfvars"


## Eliminación de recursos

Destruye los recursos creados por el stack:

terraform -chdir="$PWD\terraform\stacks\container_registry" destroy -var-file="$PWD\terraform\environments\dev\container_registry\terraform.tfvars"


# Consideraciones

- El estado se almacena en un bucket S3 remoto.
- Cada ambiente usa su propio archivo backend.tfvars para aislar el estado.
- Las variables del entorno se definen en terraform.tfvars.
- Se recomienda no subir archivos .tfstate al repositorio.

# CLUSTER EKS

terraform -chdir="$PWD\terraform\stacks\eks" init -backend-config="$PWD\terraform\environments\dev\eks\backend.tfvars"
terraform -chdir="$PWD\terraform\stacks\eks" plan -var-file="$PWD\terraform\environments\dev\eks\terraform.tfvars"
terraform -chdir="$PWD\terraform\stacks\eks" apply -var-file="$PWD\terraform\environments\dev\eks\terraform.tfvars"

## Destry para que no genere cobros

terraform -chdir="$PWD\terraform\stacks\eks" destroy -var-file="$PWD\terraform\environments\dev\eks\terraform.tfvars"


# Imagen Booking
Repo: aws ecr create-repository --repository-name booking
Img:
docker build --no-cache -t booking:1.0.2 ./src/Booking
Tag:
docker tag booking:1.0.2 962273458546.dkr.ecr.us-east-1.amazonaws.com/booking:1.0.2
Push
docker push 962273458546.dkr.ecr.us-east-1.amazonaws.com/booking:1.0.2

# Imagen Notification
Repo: aws ecr create-repository --repository-name notification
Img:
docker build --no-cache -t notification:1.0.0 ./src/Notification
Tag:
docker tag notification:1.0.0 962273458546.dkr.ecr.us-east-1.amazonaws.com/notification:1.0.0
Push
docker push 962273458546.dkr.ecr.us-east-1.amazonaws.com/notification:1.0.0

# Imagen Payment
Repo: aws ecr create-repository --repository-name payment
docker build --no-cache -t payment:1.0.4 ./src/Payment
docker tag payment:1.0.4 962273458546.dkr.ecr.us-east-1.amazonaws.com/payment:1.0.4
docker push 962273458546.dkr.ecr.us-east-1.amazonaws.com/payment:1.0.4

# Imagen pmsintegration
Repo: aws ecr create-repository --repository-name pmsintegration
docker build -t pmsintegration:1.0.4 ./src/PMSintegration
docker tag pmsintegration:1.0.4 962273458546.dkr.ecr.us-east-1.amazonaws.com/pmsintegration:1.0.4
docker push 962273458546.dkr.ecr.us-east-1.amazonaws.com/pmsintegration:1.0.4


# Imagen PartnerManagement
Repo: aws ecr create-repository --repository-name partnermanagement
docker build --no-cache -t partnermanagement:1.0.1 ./src/PartnerManagement
docker tag partnermanagement:1.0.1 962273458546.dkr.ecr.us-east-1.amazonaws.com/partnermanagement:1.0.1
docker push 962273458546.dkr.ecr.us-east-1.amazonaws.com/partnermanagement:1.0.1



# Coenctar y Actualizar kubeconfig

aws eks update-kubeconfig --region us-east-1 --name grupo12-travelhub-eks


## Desplegar Booking
kubectl apply -f ./k8s/aws/booking-deployment.yaml
kubectl apply -f ./k8s/aws/booking-service.yaml
kubectl rollout restart deployment booking-deployment

## Desplegar Notification
kubectl apply -f ./k8s/aws/notification-deployment.yaml
kubectl apply -f ./k8s/aws/notification-service.yaml


## Desplegar payment
kubectl apply -f ./k8s/aws/payment-deployment.yaml
kubectl apply -f ./k8s/aws/payment-service.yaml

## Desplegar pmsintegration
kubectl apply -f ./k8s/aws/pmsintegration-deployment.yaml
kubectl apply -f ./k8s/aws/pmsintegration-service.yaml
kubectl rollout restart deployment pmsintegration-deployment


## Desplegar PartnerManagement

kubectl apply -f ./k8s/aws/partnermanagement-deployment.yaml
kubectl apply -f ./k8s/aws/partnermanagement-service.yaml
kubectl rollout restart deployment partnermanagement-deployment

# Vuelve a loguear
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 962273458546.dkr.ecr.us-east-1.amazonaws.com


# Ingress
Se configuró un Ingress Controller (NGINX) en el cluster EKS para exponer todos los microservicios mediante una sola URL pública.

kubectl apply -f ./k8s/aws/ingress.yaml
kubectl get svc -n ingress-nginx ingress-nginx-controller -w

URL: http://a27afd6e0e6414ee490e57d925fab93e-408326643.us-east-1.elb.amazonaws.com

kubectl get pods -n ingress-nginx

Probar:
/pmsintegration/health
/payment/health
/notification/health
