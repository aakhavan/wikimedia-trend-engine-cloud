
output "msk_bootstrap_brokers_sasl_scram" {
  description = "The SASL/SCRAM connection string for the MSK cluster."
  value       = aws_msk_cluster.wikimedia_cluster.bootstrap_brokers_sasl_scram
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