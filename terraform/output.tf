
output "msk_bootstrap_brokers_iam" {
  description = "The SASL/IAM connection string for the MSK cluster."
  value       = aws_msk_cluster.wikimedia_cluster.bootstrap_brokers_sasl_iam
  sensitive   = true
}

output "data_lake_s3_bucket_name" {
  description = "The name of the S3 bucket for the data lake."
  value       = aws_s3_bucket.data_lake.bucket
}

output "glue_database_name" {
  description = "The name of the Glue Catalog database."
  value       = aws_glue_catalog_database.wikimedia_db.name
}

output "spark_execution_role_arn" {
  description = "The ARN of the IAM role for Spark jobs."
  value       = aws_iam_role.spark_execution_role.arn
}

output "dev_instance_public_ip" {
  description = "Public IP address of the development EC2 instance."
  value       = aws_instance.dev_instance.public_ip
}

output "ssh_command" {
  description = "Command to SSH into the development EC2 instance."
  value       = "ssh -i ${local_file.dev_private_key.filename} ec2-user@${aws_instance.dev_instance.public_ip}"
  sensitive   = true
}