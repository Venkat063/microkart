variable "environment" {
  type        = string
  description = "dev | staging | prod"
}

variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "single_nat_gateway" {
  type        = bool
  default     = true
  description = "One shared NAT (cheap, dev) vs one per AZ (HA, prod)"
}

variable "cluster_version" {
  type    = string
  default = "1.31"
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.large"]
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_capacity_type" {
  type        = string
  default     = "ON_DEMAND"
  description = "ON_DEMAND or SPOT"
}

variable "api_public_access_cidrs" {
  type        = list(string)
  default     = []
  description = "CIDRs allowed to reach the EKS API endpoint. Empty = private endpoint only (needs VPN/bastion)."
}

variable "admin_role_arns" {
  type        = list(string)
  default     = []
  description = "IAM roles/users granted cluster-admin through EKS access entries (SSO admin role, CI role)"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.small"
}

variable "db_allocated_storage" {
  type    = number
  default = 20
}

variable "db_max_allocated_storage" {
  type    = number
  default = 100
}

variable "db_multi_az" {
  type    = bool
  default = false
}

variable "db_backup_retention_days" {
  type    = number
  default = 7
}

variable "deletion_protection" {
  type    = bool
  default = false
}

variable "secret_recovery_window_days" {
  type    = number
  default = 0
}
