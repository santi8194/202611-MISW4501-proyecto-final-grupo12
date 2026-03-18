module "ecr_repository" {
  source = "../../modules/repository"
  keep_tags_number = var.keep_tags_number
  repository_name  = var.repository_name
}