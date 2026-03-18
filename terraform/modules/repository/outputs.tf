output "repository_arn" {
  value       = aws_ecr_repository.main.arn # nombre, tipo y atributo del recurso
  description = "Repository ARN."
}