output "cluster_name" {
  value       = module.eks.cluster_name
  description = "Name of the EKS cluster"
}

output "cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "Endpoint URL of the EKS cluster API server"
}

output "cluster_certificate_authority_data" {
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
  description = "Base64-encoded certificate authority data for the cluster"
}

output "configure_kubectl" {
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
  description = "Run this command to configure kubectl to access the cluster"
}
