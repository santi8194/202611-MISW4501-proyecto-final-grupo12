# cicd.tf
# Owner: Miembro 3 (Data + DevOps)

# Objetivo:
# Definir pipeline CI/CD en AWS para desplegar servicios ECS y Lambda.

# TODO [CI/CD-1]: bucket S3 de artefactos para pipelines (con cifrado)
# TODO [CI/CD-2]: KMS key para artefactos y logs (opcional segun politica)
# TODO [CI/CD-3]: IAM roles para CodePipeline y CodeBuild con minimo privilegio

# TODO [CI/CD-4]: conexion a repositorio fuente (CodeStar Connections / CodeCommit)
# TODO [CI/CD-5]: pipeline de build y push de imagenes a ECR
# TODO [CI/CD-6]: pipeline de despliegue ECS (booking/payments/partner/search/saga)
# TODO [CI/CD-7]: pipeline de despliegue Lambda (sync)

# TODO [CI/CD-8]: proyectos CodeBuild con buildspec para:
# - tests + lint
# - build contenedores
# - terraform plan/apply por ambiente (si aplica)

# TODO [CI/CD-9]: aprobaciones manuales para prod + notificaciones (SNS/ChatOps)
# TODO [CI/CD-10]: estrategia por ambientes (dev/stg/prod) y promotion gates
# TODO [CI/CD-11]: gates de calidad pre-deploy:
# - migraciones exitosas
# - smoke tests de conectividad a DB
# - validacion de esquemas/indices
# - rollback o bloqueo de promotion si falla
