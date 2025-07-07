
resource "aws_glue_catalog_database" "wikimedia_db" {
  name = "${local.project_name}-db"

  tags = local.common_tags
}