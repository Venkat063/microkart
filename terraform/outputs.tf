output "cluster_name" { value = module.eks.cluster_name }
output "region" { value = var.region }
output "eso_role_arn" { value = module.eso_irsa.iam_role_arn }
output "rds_endpoint" { value = module.rds.db_instance_address }
output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.region}"
}
