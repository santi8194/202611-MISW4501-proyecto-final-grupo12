output "eks_cluster_id" {
  description = "El ID del clúster EKS desplegado."
  value       = module.my_eks_cluster.cluster_id 
}

output "eks_cluster_arn" {
  description = "El ARN del clúster EKS desplegado."
  value       = module.my_eks_cluster.cluster_arn 
}

output "eks_cluster_endpoint" {
  description = "El endpoint del clúster EKS desplegado."
  value       = module.my_eks_cluster.cluster_endpoint 
}

output "eks_cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data para conectarse al clúster EKS."
  value       = module.my_eks_cluster.cluster_certificate_authority_data 
  sensitive   = true
}

output "eks_cluster_oidc_issuer_url" {
  description = "La URL del OpenID Connect identity provider del clúster EKS."
  value       = module.my_eks_cluster.cluster_oidc_issuer_url #
}

output "eks_node_group_autoscaling_group_names" {
  description = "Nombres de los Auto Scaling Groups de los nodos gestionados por EKS."
  value       = module.my_eks_cluster.eks_managed_node_groups_autoscaling_group_names 
}