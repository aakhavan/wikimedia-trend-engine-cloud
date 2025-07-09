
variable "aws_region" {
  description = "The AWS region where resources will be created."
  type        = string
  default     = "eu-central-1"
}

variable "availability_zones_count" {
  description = "The number of Availability Zones to use for the VPC. Should be at least 2 for high availability."
  type        = number
  default     = 2
}