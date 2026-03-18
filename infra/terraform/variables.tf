# Variables compartidas (base)
# TODO [Shared]: completar segun necesidades de cada modulo

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "travelhub"
}

variable "environment" {
  description = "Ambiente"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "Region AWS"
  type        = string
  default     = "us-east-1"
}

# TODO [Miembro 1]: variables de red, edge y seguridad perimetral
# TODO [Miembro 2]: variables de ECS, Lambda y autoscaling
# TODO [Miembro 3]: variables de RDS, DynamoDB, MQ y OpenSearch

# TODO [CI/CD]: variables DevOps AWS
# Ejemplos sugeridos:
# - enable_cicd
# - source_provider (codestar|codecommit)
# - codestar_connection_arn
# - repository_owner / repository_name / repository_branch
# - ecr_repository_names
# - artifact_bucket_force_destroy
# - enable_manual_approval_prod
