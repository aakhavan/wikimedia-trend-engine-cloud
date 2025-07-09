# IAM Role for Spark Jobs to assume
resource "aws_iam_role" "spark_execution_role" {
  name = "${local.project_name}-spark-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Policy granting access to the S3 data lake bucket
resource "aws_iam_policy" "s3_access_policy" {
  name        = "${local.project_name}-s3-access-policy"
  description = "Allows read/write access to the S3 data lake bucket"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ],
        Effect = "Allow",
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*" # Important: Grant access to objects within the bucket
        ]
      }
    ]
  })
}

# Policy granting access to the AWS Glue Data Catalog
resource "aws_iam_policy" "glue_access_policy" {
  name        = "${local.project_name}-glue-access-policy"
  description = "Allows Spark to interact with the AWS Glue Data Catalog for Iceberg tables"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:GetPartitions",
          "glue:CreatePartition",
          "glue:BatchCreatePartition",
          "glue:DeletePartition",
          "glue:BatchDeletePartition"
        ],
        Effect   = "Allow",
        Resource = "*" # For simplicity. In a production environment, you would lock this down to specific catalog/db/table ARNs.
      }
    ]
  })
}

# Attach the S3 policy to the Spark role
resource "aws_iam_role_policy_attachment" "attach_s3_policy" {
  role       = aws_iam_role.spark_execution_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

# Attach the Glue policy to the Spark role
resource "aws_iam_role_policy_attachment" "attach_glue_policy" {
  role       = aws_iam_role.spark_execution_role.name
  policy_arn = aws_iam_policy.glue_access_policy.arn
}