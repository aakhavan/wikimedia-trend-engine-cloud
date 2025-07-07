
# Defines a security group to act as a virtual firewall for the MSK cluster.
resource "aws_security_group" "msk_sg" {
  name        = "${local.project_name}-msk-sg"
  description = "Security group for MSK cluster"
  vpc_id      = module.vpc.vpc_id

  # This ingress rule allows any resource inside our VPC to communicate
  # with the MSK brokers. This is essential for our producer and Spark jobs.
  # In a production environment, you would tighten this to only allow traffic
  # from the specific security groups of your applications.
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  # Allows brokers to communicate with the outside world (e.g., for AWS APIs).
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

# Defines a reusable configuration for the Kafka cluster.
# This allows us to manage server properties centrally.
resource "aws_msk_configuration" "kafka_config" {
  name              = "${local.project_name}-kafka-config"
  kafka_versions    = ["3.5.1"] # Must match the cluster's Kafka version.
  server_properties = <<-EOT
    auto.create.topics.enable = true
    delete.topic.enable = true
  EOT
}

# Defines the actual MSK Kafka cluster resource.
resource "aws_msk_cluster" "wikimedia_cluster" {
  cluster_name           = "${local.project_name}-cluster"
  kafka_version          = "3.5.1" # Must match the version in aws_msk_configuration
  number_of_broker_nodes = var.availability_zones_count

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    client_subnets  = module.vpc.private_subnets
    security_groups = [aws_security_group.msk_sg.id]

    storage_info {
      ebs_storage_info {
        volume_size = 10 # Defines the size in GiB for each broker's EBS volume
      }
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.kafka_config.arn
    revision = aws_msk_configuration.kafka_config.latest_revision
  }

  # Enable SASL/SCRAM for secure authentication. This is a best practice.
  client_authentication {
    sasl {
      scram = true
    }
  }

  tags = local.common_tags
}
