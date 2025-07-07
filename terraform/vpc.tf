
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.8.1"

  name = "${local.project_name}-vpc"
  cidr = "10.0.0.0/16"

  # Use the number of availability zones defined in variables.tf
  azs             = slice(data.aws_availability_zones.available.names, 0, var.availability_zones_count)
  private_subnets = [for k, v in slice(data.aws_availability_zones.available.names, 0, var.availability_zones_count) : "10.0.${k + 1}.0/24"]
  public_subnets  = [for k, v in slice(data.aws_availability_zones.available.names, 0, var.availability_zones_count) : "10.0.${k + 101}.0/24"]

  # Enable a NAT Gateway to allow resources in private subnets (like our Spark jobs)
  # to access the internet for things like downloading packages, without being publicly accessible.
  enable_nat_gateway = true
  single_nat_gateway = true # For cost savings in dev. Set to false for higher availability in production.

  tags = local.common_tags
}