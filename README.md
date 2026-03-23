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
Img:
docker build -t booking:1.0.0 ./src/Booking
Tag:
docker tag booking:1.0.0 962273458546.dkr.ecr.us-east-1.amazonaws.com/container-registry-dev:1.0.0
Push
docker push 962273458546.dkr.ecr.us-east-1.amazonaws.com/container-registry-dev:1.0.0

# Imagen Notification
Img:
docker build -t notification:1.0.0 ./src/Notification
Tag:
docker tag notification:1.0.0 962273458546.dkr.ecr.us-east-1.amazonaws.com/container-registry-dev:1.0.0
Push
docker push 962273458546.dkr.ecr.us-east-1.amazonaws.com/container-registry-dev:1.0.0

# Coenctar desde kubectl

aws eks update-kubeconfig --region us-east-1 --name grupo12-travelhub-eks


## Desplegar Booking
kubectl apply -f ./src/k8s/aws/booking-deployment.yaml
kubectl apply -f ./src/k8s/aws/booking-service.yaml


# Vuelve a loguear
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 962273458546.dkr.ecr.us-east-1.amazonaws.com