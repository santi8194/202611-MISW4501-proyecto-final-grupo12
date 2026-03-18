# Plan de Trabajo - 3 Miembros (Balanceado)

## Miembro 1 - Plataforma/Edge

Archivos propuestos:

- `networking.tf`
- `security.tf`
- `api.tf`

Responsabilidades:

- Red multi-AZ (VPC, subredes, rutas, NAT)
- Seguridad perimetral y por capas (SG, reglas)
- API Gateway + WAF + Cognito + integracion con ALB

Entregables:

- Conectividad edge -> runtime validada
- Autenticacion/autorizacion base operativa
- Hardening inicial de entrada y rate limiting

## Miembro 2 - Runtime

Archivos propuestos:

- `compute.tf`
- `serverless.tf`

Responsabilidades:

- ECS Fargate para servicios core
- Autoescalado por servicio
- Sync Service en Lambda
- IAM runtime de workloads

Entregables:

- Servicios en estado estable
- Policias runtime minimas necesarias
- Healthchecks y puertos de servicio definidos

## Miembro 3 - Data + DevOps

Archivos propuestos:

- `database.tf`
- `messaging.tf`
- `cicd.tf`
- `outputs.tf`

Responsabilidades:

- Persistencia: RDS, DynamoDB, OpenSearch
- Mensajeria: Amazon MQ + SNS
- CI/CD AWS: CodeBuild/CodePipeline/ECR
- Gates de calidad pre-deploy en pipeline

Entregables:

- Endpoints/ARNs de datos y eventos publicados en outputs
- Pipelines de build/deploy por ambiente
- Promotion gates (checks + rollback/bloqueo)

## Reglas compartidas

- `providers.tf`, `variables.tf`, `locals.tf`, `data.tf`, `terraform.tfvars.example` se modifican por consenso en PR corto.
- Toda PR debe pasar:
  - `terraform fmt -recursive`
  - `terraform validate`
- No mezclar cambios de ownership sin aviso en la PR.
