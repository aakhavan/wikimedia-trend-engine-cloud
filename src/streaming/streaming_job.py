import os
import yaml
import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.streaming import StreamingQuery

# Import our new, isolated transformation function
from src.streaming.transformations import transform_wikimedia_stream

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SparkStreamingJob:
    """
    A class to orchestrate a Spark Structured Streaming job. It is responsible
    for session creation, reading from Kafka, and writing to Iceberg, but
    delegates the transformation logic to a separate, pure function.
    """

    def __init__(self, config_path='config/config.yml'):
        """Initializes the job by loading configuration."""
        self.config = self._load_config(config_path)
        self.spark = self._create_spark_session()
        logging.info("SparkStreamingJob initialized.")

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
        logging.info("Creating Spark session...")
        s3_bucket = os.environ.get('DATA_LAKE_BUCKET')
        if not s3_bucket:
            raise ValueError("Environment variable DATA_LAKE_BUCKET is not set.")

        glue_db_name = os.environ.get('GLUE_DB_NAME')
        if not glue_db_name:
            raise ValueError("Environment variable GLUE_DB_NAME is not set.")

        s3_warehouse_path = f"s3a://{s3_bucket}{self.config['iceberg']['warehouse_path']}"

        spark = (
            SparkSession.builder.appName(self.config['spark']['app_name'])
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
            .config(f"spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
            .config(f"spark.sql.catalog.glue_catalog.warehouse", s3_warehouse_path)
            .config(f"spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
            .config(f"spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
            .getOrCreate()
        )
        logging.info("Spark session created successfully.")
        return spark

    def _read_from_kafka(self) -> DataFrame:
        """Reads data from the MSK Kafka topic as a streaming DataFrame."""
        msk_bootstrap_servers = os.environ.get('MSK_BOOTSTRAP_SERVERS')
        if not msk_bootstrap_servers:
            raise ValueError("Environment variable MSK_BOOTSTRAP_SERVERS is not set.")

        logging.info(f"Reading from Kafka topic: {self.config['kafka']['topic_name']}")
        return (
            self.spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", msk_bootstrap_servers)
            .option("subscribe", self.config['kafka']['topic_name'])
            .option("kafka.security.protocol", "SASL_SSL")
            .option("kafka.sasl.mechanism", "AWS_MSK_IAM")
            .option("kafka.sasl.jaas.config", "software.amazon.msk.auth.iam.IAMLoginModule required;")
            .option("kafka.sasl.client.callback.handler.class", "software.amazon.msk.auth.iam.IAMClientCallbackHandler")
            .load()
        )

    def run(self):
        """Orchestrates the streaming pipeline: read, transform, and write."""
        try:
            glue_db_name = os.environ.get('GLUE_DB_NAME')
            s3_bucket = os.environ.get('DATA_LAKE_BUCKET')
            table_name = self.config['iceberg']['stream_table_name']
            full_table_name = f"glue_catalog.{glue_db_name}.{table_name}"
            checkpoint_location = f"s3a://{s3_bucket}{self.config['spark']['checkpoint_location_base']}{table_name}"

            # NOTE: The schema definition and transformation logic have been moved out.
            # This class no longer needs to know about them.

            kafka_stream_df = self._read_from_kafka()

            # Call the pure transformation function from the other file
            transformed_df = transform_wikimedia_stream(kafka_stream_df)

            logging.info(f"Starting stream write to Iceberg table: {full_table_name}")
            query = (
                transformed_df.writeStream
                .format("iceberg")
                .outputMode("append")
                .trigger(processingTime='60 seconds')
                .option("path", full_table_name)
                .option("checkpointLocation", checkpoint_location)
                .start()
            )

            query.awaitTermination()
        except Exception as e:
            logging.error("An error occurred during the streaming job.", exc_info=True)
            raise


if __name__ == "__main__":
    job = SparkStreamingJob()
    job.run()