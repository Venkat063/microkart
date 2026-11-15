bucket         = "REPLACE_WITH_STATE_BUCKET"  # terraform -chdir=bootstrap output state_bucket
key            = "microkart/staging/terraform.tfstate"
region         = "ap-south-1"
dynamodb_table = "microkart-tflock"
encrypt        = true
