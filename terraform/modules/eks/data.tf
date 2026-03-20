data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "all" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name   = "availability-zone"
    values = ["us-east-1a", "us-east-1b", "us-east-1c", "us-east-1d"]
  }
}

data "aws_iam_roles" "eks_cluster" {
  name_regex = "LabEksClusterRole"
}

data "aws_iam_roles" "eks_node" {
  name_regex = "LabEksNodeRole"
}

data "aws_iam_roles" "lab_role" {
  name_regex = "LabRole"
}