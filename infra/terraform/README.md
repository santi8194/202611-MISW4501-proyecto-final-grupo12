# Terraform Skeleton Guide - TravelHub

Este README define convenciones y reglas de trabajo. El detalle de reparto de tareas vive en `PLAN_TRABAJO_3_MIEMBROS.md`.

## Convencion de nombres

Patron oficial:

`th-{env}-{dominio}-{componente}`

Reglas:

- Usar `kebab-case`, minusculas, sin tildes.
- `env` permitido: `dev`, `stg`, `prod`.
- Reusar el mismo patron en ECS, Lambda, RDS, MQ, IAM y CI/CD.

Ejemplos:

- `th-dev-booking-api`
- `th-dev-saga-orchestrator`
- `th-prod-sync-adapter`
- `th-prod-cicd-release`

## Tags obligatorios

Aplicar en todos los recursos:

- `Project = travelhub`
- `Environment = <dev|stg|prod>`
- `Owner = <miembro|equipo>`
- `ManagedBy = terraform`
- `CostCenter = <definir>`
- `DataClass = <public|internal|restricted>`

## IAM y permisos

Reglas base:

- Minimo privilegio por defecto.
- Nada de permisos wildcard sin justificacion en PR.
- Separar roles por contexto: edge, runtime, data, cicd.
- No guardar secretos en codigo ni en `terraform.tfvars` versionado.

Ownership IAM (operativo):

- Miembro 1: IAM de edge/plataforma (API Gateway, Cognito, perimetro).
- Miembro 2: IAM de runtime (ECS tasks y Lambda sync).
- Miembro 3: IAM de CI/CD (CodeBuild, CodePipeline, ECR, artefactos).

Decision de gobierno recomendada:

- Miembro 1 valida PRs de IAM como revisor obligatorio.

## Seguridad minima de entrada (hardening)

- TLS 1.2+ en endpoints expuestos.
- WAF administrado + rate limit.
- SG restringidos a trafico necesario.
- Autenticacion JWT/OIDC en edge.
- Logs de acceso habilitados para API/ALB/WAF.

## Reglas Terraform

- Mantener ownership de archivos segun el plan.
- Evitar duplicar logica: usar `locals`, `for_each`, mapas.
- Todos los cambios deben pasar:
  - `terraform fmt -recursive`
  - `terraform validate`
- Nunca commitear credenciales o secretos.

## CI/CD (referencia)

El esqueleto de CI/CD esta en `cicd.tf` con TODOs para:

- Source connection
- Build/test
- Push a ECR
- Deploy ECS/Lambda
- Promotion gates y rollback