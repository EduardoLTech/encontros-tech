variable "region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region to deploy into"
}

variable "project_name" {
  type        = string
  default     = "encontros-tech"
  description = "Name prefix used for tagging and resource naming"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the VPC"
}

variable "azs" {
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
  description = "Availability zones to spread subnets across (must match region)"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
  description = "CIDR blocks for private subnets (one per AZ, used for EKS nodes)"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
  description = "CIDR blocks for public subnets (one per AZ, used for NAT gateway/load balancers)"
}

variable "cluster_name" {
  type        = string
  default     = "encontros-tech"
  description = "Name of the EKS cluster"
}

variable "cluster_version" {
  type        = string
  default     = "1.30"
  description = "Kubernetes version for the EKS control plane"
}

variable "node_instance_type" {
  type        = string
  default     = "t3.medium"
  description = "EC2 instance type for the EKS managed node group (2 vCPU / 4 GiB, sized for the app's ~750m CPU / ~768Mi workload plus EKS system daemonset overhead)"
}

variable "node_desired_size" {
  type        = number
  default     = 2
  description = "Desired number of worker nodes"
}

variable "node_min_size" {
  type        = number
  default     = 1
  description = "Minimum number of worker nodes"
}

variable "node_max_size" {
  type        = number
  default     = 3
  description = "Maximum number of worker nodes"
}

variable "cluster_endpoint_public_access" {
  type        = bool
  default     = true
  description = "Whether the EKS public API endpoint is enabled"
}
