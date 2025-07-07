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
  region = "us-east-1" # You can change this to your preferred region
}

# ===================================================================
# Data Sources
# ===================================================================
# Get the current AWS Account ID to use in resource names and policies
data "aws_caller_identity" "current" {}

# Get a list of Availability Zones in the current region
# This makes our VPC resilient by default.
data "aws_availability_zones" "available" {}

# ===================================================================
# Resource Naming Convention
# ===================================================================
# Use a consistent naming prefix for all resources for easy identification.
locals {
  project_name = "wikimedia-trends"
  common_tags = {
    Project   = local.project_name
    ManagedBy = "Terraform"
  }
}