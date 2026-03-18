#https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html
# política que define cuantas imágenes serán preservadas en el repositorio.
locals {
  policy_document = <<EOF
  {
    "rules": [
      {
        "rulePriority": 1,
        "description": "Keep last ${var.keep_tags_number} images",
        "selection": {
          "tagStatus": "any",
          "countType": "imageCountMoreThan",
          "countNumber": ${var.keep_tags_number}
        },
        "action": {
          "type": "expire"
        }
      }
    ]
  }
  EOF
}