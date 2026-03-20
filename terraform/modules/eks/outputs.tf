output "cluster_id" {
  description = "ID (y nombre) del clúster EKS."
  value       = module.eks_cluster.cluster_id
}

output "cluster_arn" {
  description = "ARN completo del clúster EKS."
  value       = module.eks_cluster.cluster_arn
}

output "cluster_endpoint" {
  description = "URL del API server del clúster."
  value       = module.eks_cluster.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "Certificado CA (base64) para hablar con el clúster."
  value       = module.eks_cluster.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_oidc_issuer_url" {
  description = "URL del proveedor OIDC del clúster."
  value       = module.eks_cluster.cluster_oidc_issuer_url
}

output "cluster_security_group_id" {
  description = "Security Group principal que protege el plano de control."
  value       = module.eks_cluster.cluster_security_group_id
}

output "cluster_name_output" {
  description = "Nombre del clúster (alias de cluster_id)."
  value       = module.eks_cluster.cluster_id
}

output "eks_managed_node_groups_autoscaling_group_names" {
  description = "Nombres de los Auto Scaling Groups creados por los managed node groups."
  value       = module.eks_cluster.eks_managed_node_groups_autoscaling_group_names
}