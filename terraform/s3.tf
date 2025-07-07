# Defines the S3 bucket that will serve as our data lake.
# The bucket name is constructed to be globally unique by appending the AWS Account ID.
resource "aws_s3_bucket" "data_lake" {
  bucket = "${local.project_name}-data-lake-${data.aws_caller_identity.current.account_id}"

  tags = local.common_tags
}

# Enables versioning on the S3 bucket.
# This is a critical best practice for a data lake to prevent accidental data deletion
# and allow for recovery of previous versions of data objects.
resource "aws_s3_bucket_versioning" "data_lake_versioning" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enforces server-side encryption (SSE) for all objects written to the bucket.
# This ensures that all data is encrypted at rest, a fundamental security requirement.
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake_sse" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Blocks all public access to the bucket.
# This is a crucial security measure to ensure our private data lake
# is not accidentally exposed to the internet.
resource "aws_s3_bucket_public_access_block" "data_lake_public_access" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}