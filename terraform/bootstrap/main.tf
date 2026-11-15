# One-time, per AWS account. Creates: remote-state bucket + lock table, ECR repo per service,
# GitHub OIDC provider and the CI roles (no long-lived AWS keys anywhere).
# Run with local state first:  terraform init && terraform apply -var github_repo=ORG/REPO

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.80" }
  }
}

variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository allowed to assume the CI roles, as ORG/REPO"
}

variable "state_bucket_name" {
  type        = string
  default     = null
  description = "Override the default microkart-tfstate-<account-id> bucket name"
}

provider "aws" {
  region = var.region
  default_tags { tags = { Project = "microkart", ManagedBy = "terraform", Stack = "bootstrap" } }
}

data "aws_caller_identity" "me" {}

locals {
  account_id    = data.aws_caller_identity.me.account_id
  bucket        = coalesce(var.state_bucket_name, "microkart-tfstate-${local.account_id}")
  service_names = [for s in flatten([for d in yamldecode(file("${path.module}/../../services.yaml")).domains : d.services]) : s]
}

# ---------------- remote state
resource "aws_s3_bucket" "state" {
  bucket = local.bucket
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "lock" {
  name         = "microkart-tflock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
}

# ---------------- container registry: one immutable-tag repo per service (shared by all environments)
resource "aws_ecr_repository" "svc" {
  for_each             = toset(local.service_names)
  name                 = "microkart/${each.key}"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
}

resource "aws_ecr_lifecycle_policy" "svc" {
  for_each   = aws_ecr_repository.svc
  repository = each.value.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the 50 most recent images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 50 }
      action       = { type = "expire" }
    }]
  })
}

# ---------------- GitHub OIDC + CI roles
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "ecr_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:ref:refs/heads/main"] # only main can push images
    }
  }
}

resource "aws_iam_role" "ci_ecr" {
  name               = "microkart-github-ecr"
  assume_role_policy = data.aws_iam_policy_document.ecr_trust.json
}

data "aws_iam_policy_document" "ecr_push" {
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    actions = [
      "ecr:BatchCheckLayerAvailability", "ecr:BatchGetImage", "ecr:CompleteLayerUpload",
      "ecr:DescribeImages", "ecr:GetDownloadUrlForLayer", "ecr:InitiateLayerUpload",
      "ecr:PutImage", "ecr:UploadLayerPart",
    ]
    resources = ["arn:aws:ecr:${var.region}:${local.account_id}:repository/microkart/*"]
  }
}

resource "aws_iam_role_policy" "ci_ecr" {
  role   = aws_iam_role.ci_ecr.id
  policy = data.aws_iam_policy_document.ecr_push.json
}

data "aws_iam_policy_document" "tf_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_repo}:pull_request",
        "repo:${var.github_repo}:environment:*", # apply runs behind GitHub Environment approvals
      ]
    }
  }
}

# Terraform needs broad rights to build VPC/EKS/RDS/IAM. Narrow this once the stack stabilises.
resource "aws_iam_role" "ci_terraform" {
  name               = "microkart-github-terraform"
  assume_role_policy = data.aws_iam_policy_document.tf_trust.json
}

resource "aws_iam_role_policy_attachment" "ci_terraform" {
  role       = aws_iam_role.ci_terraform.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

output "state_bucket" { value = aws_s3_bucket.state.id }
output "lock_table" { value = aws_dynamodb_table.lock.name }
output "ecr_registry" { value = "${local.account_id}.dkr.ecr.${var.region}.amazonaws.com/microkart" }
output "ci_ecr_role_arn" { value = aws_iam_role.ci_ecr.arn }
output "ci_terraform_role_arn" { value = aws_iam_role.ci_terraform.arn }
