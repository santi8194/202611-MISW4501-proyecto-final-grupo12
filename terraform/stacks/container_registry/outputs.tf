output "repository_arn" {
  value       = module.ecr_repository.repository_arn # nombre, tipo y atributo del recurso
  description = "Created repository ARN."
}