module "my_eks_cluster" {
  source = "../../modules/eks"

  cluster_name                   = var.cluster_name
  k8s_cluster_version            = var.k8s_cluster_version
  cluster_endpoint_public_access = var.cluster_endpoint_public_access
}
