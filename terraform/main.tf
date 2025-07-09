# ===================================================================
# AWS Provider and Backend Configuration
# ===================================================================
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
}

data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {}

locals {
  project_name = "wikimedia-trends"
  common_tags = {
    Project   = local.project_name
    ManagedBy = "Terraform"
  }
}