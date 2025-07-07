import os
import yaml
import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.functions import col, to_timestamp, date_trunc, count, from_utc_timestamp, to_utc_timestamp



# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class WikimediaBatchJob:
    """
    A batch processing job that reads from a raw Iceberg table, performs
    hourly aggregations, and writes the results to a summary Iceberg table.
    """

    def __init__(self, config_path='config/config.yml'):
        """Initializes the job by loading configuration and creating a SparkSession."""
        self.config = self._load_config(config_path)
        self.spark = self._create_spark_session()
        logging.info("WikimediaBatchJob initialized.")

    def _load_config(self, path):
        """Loads the YAML configuration file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.error("Configuration file not found at path: %s", path)
            raise

    def _create_spark_session(self):
        """Creates and configures a SparkSession with Iceberg and Glue Catalog support."""
        logging.info("Creating Spark session for batch job...")
        s3_bucket = os.environ.get('DATA_LAKE_BUCKET')
        if not s3_bucket:
            raise ValueError("Environment variable DATA_LAKE_BUCKET is not set.")

        glue_db_name = os.environ.get('GLUE_DB_NAME')
        if not glue_db_name:
            raise ValueError("Environment variable GLUE_DB_NAME is not set.")

        s3_warehouse_path = f"s3a://{s3_bucket}{self.config['iceberg']['warehouse_path']}"

        # The configuration is identical to the streaming job, ensuring consistency
        spark = (
            SparkSession.builder.appName(self.config['spark']['app_name'] + "Batch")
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
            .config(f"spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
            .config(f"spark.sql.catalog.glue_catalog.warehouse", s3_warehouse_path)
            .config(f"spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
            .config(f"spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
            .getOrCreate()
        )
        logging.info("Spark session for batch job created successfully.")
        return spark

    @staticmethod
    def transform_data(raw_df: DataFrame) -> DataFrame:
        """
        Performs the core aggregation logic for the batch job.
        - Filters for 'edit' events.
        - Calculates the event hour in UTC.
        - Counts edits per domain per hour.
        """
        logging.info("Applying batch transformations.")
        return (
            raw_df
            .filter(col("type") == "edit")
            .withColumn(
                "event_hour",
                date_trunc(
                    "hour",
                    to_timestamp(col("meta.dt"))
                )
            )
            .groupBy("event_hour", col("meta.domain").alias("domain"))
            .agg(count("*").alias("edit_count"))
        )


    def run(self):
        """Orchestrates the batch job: read, transform, and write."""
        try:
            glue_db_name = os.environ.get('GLUE_DB_NAME')
            source_table_name = self.config['iceberg']['stream_table_name']
            target_table_name = self.config['iceberg']['batch_table_name']

            full_source_name = f"glue_catalog.{glue_db_name}.{source_table_name}"
            full_target_name = f"glue_catalog.{glue_db_name}.{target_table_name}"

            logging.info(f"Reading from source table: {full_source_name}")
            raw_data_df = self.spark.read.table(full_source_name)

            aggregated_df = self.transform_data(raw_data_df)

            logging.info(f"Writing aggregated data to target table: {full_target_name}")
            # This write operation is idempotent. Rerunning the job for the same
            # period will simply overwrite the results, ensuring correctness.
            (
                aggregated_df.write
                .format("iceberg")
                .mode("overwrite")
                .saveAsTable(full_target_name)
            )

            logging.info("Batch job completed successfully.")

        except Exception as e:
            logging.error("An error occurred during the batch job.", exc_info=True)
            raise


if __name__ == "__main__":
    job = WikimediaBatchJob()
    job.run()