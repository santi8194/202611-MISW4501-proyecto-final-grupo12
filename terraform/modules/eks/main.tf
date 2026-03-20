module "eks_cluster" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 18.31"             

  cluster_name    = var.cluster_name       
  cluster_version = var.k8s_cluster_version    
  vpc_id          = data.aws_vpc.default.id
  subnet_ids      = data.aws_subnets.all.ids

  cluster_endpoint_public_access = var.cluster_endpoint_public_access  

  create_iam_role = true

  eks_managed_node_groups = {
    default = {
      create_iam_role = true
      ami_type       = "AL2023_x86_64_STANDARD" # Si esto se podrá modificar convierta esto en una variable
      instance_types = ["t3.large"] # Si esto se podrá modificar convierta esto en una variable
      desired_size   = 2 # Si esto se podrá modificar< convierta esto en una variable
      min_size       = 1 # Si esto se podrá modificar convierta esto en una variable
      max_size       = 3 # Si esto se podrá modificar convierta esto en una variable
    }
  }


  node_security_group_additional_rules = {

    # Esta regla es necesaria para que el webhook de admission controller funcione correctamente 
    ingress_control_plane_to_nodes_webhook = {
      description                   = "Allow EKS Control Plane to connect to Ingress webhook"
      protocol                      = "tcp"
      from_port                     = 8443
      to_port                       = 8443
      type                          = "ingress"
      # Esta variable especial proporcionada por el módulo EKS se refiere al SG del plano de control
      source_cluster_security_group = true
    }

    ingress_nodes_to_nodes_all_traffic = {
      description = "Allow nodes to communicate with each other on all ports"
      protocol    = "-1" # "-1" indica todos los protocolos
      from_port   = 0    # 0 significa todos los puertos
      to_port     = 0    # 0 significa todos los puertos
      type        = "ingress"
      self        = true
    }

    egress_nodes_to_internet = {
      description = "Allow nodes to connect to the internet for connecting to DB and call the ingress"
      protocol    = "-1"      # todos los protocolos
      from_port   = 0         # todos los puertos
      to_port     = 0         # todos los puertos
      type        = "egress"
      cidr_blocks = ["0.0.0.0/0"] # Representa todo el tráfico de salida
    }
  }

  enable_irsa = false 
  create_aws_auth_configmap = false
  manage_aws_auth_configmap = false
}