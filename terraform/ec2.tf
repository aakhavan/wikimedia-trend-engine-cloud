# Security group for the development EC2 instance
resource "aws_security_group" "dev_ec2_sg" {
  name        = "${local.project_name}-dev-ec2-sg"
  description = "Allow SSH access to the development EC2 instance"
  vpc_id      = module.vpc.vpc_id

  # Allow SSH traffic from anywhere.
  # For better security in production, you would restrict this to your own IP.
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic so the instance can connect to MSK,
  # download packages, and access other AWS services.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

# IAM instance profile to attach our existing execution role to the EC2 instance
resource "aws_iam_instance_profile" "spark_instance_profile" {
  name = "${local.project_name}-spark-instance-profile"
  role = aws_iam_role.spark_execution_role.name
}

# A key pair is required to SSH into the EC2 instance.
# This creates a new key pair and saves the private key locally.
resource "tls_private_key" "dev_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "dev_key_pair" {
  key_name   = "${local.project_name}-dev-key"
  public_key = tls_private_key.dev_key.public_key_openssh
}

# Save the private key to a local file.
# IMPORTANT: This file is sensitive. Your .gitignore already correctly
# ignores *.pem files, so it will not be committed to your repository.
resource "local_file" "dev_private_key" {
  content         = tls_private_key.dev_key.private_key_pem
  filename        = "${path.module}/../${local.project_name}-dev-key.pem"
  file_permission = "0400" # Read-only for the user
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"] # Trust official Amazon images

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 instance for development and running the producer/Spark jobs
resource "aws_instance" "dev_instance" {
  # Use a recent Amazon Linux 2023 AMI for eu-central-1
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.micro"

  # Place the instance in the first public subnet so we can SSH into it
  subnet_id = module.vpc.public_subnets[0]

  associate_public_ip_address = true

  root_block_device {
    volume_size = 30 # Size in GiB
  }

  # Associate the security group
  vpc_security_group_ids = [aws_security_group.dev_ec2_sg.id]

  # Associate the IAM role via the instance profile
  iam_instance_profile = aws_iam_instance_profile.spark_instance_profile.name

  # Associate the key pair for SSH access
  key_name = aws_key_pair.dev_key_pair.key_name

  # Ensure the key pair is created before the instance
  depends_on = [aws_key_pair.dev_key_pair]

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-dev-instance"
    }
  )
}