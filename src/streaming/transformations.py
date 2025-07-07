from pyspark.sql import DataFrame
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType, LongType

# Define the schema for the incoming Wikimedia JSON data.
# Placing it here makes it independent and easily reusable.
WIKIMEDIA_SCHEMA = StructType([
    StructField("meta", StructType([
        StructField("id", StringType(), True),
        StructField("dt", StringType(), True),
        StructField("domain", StringType(), True),
    ]), True),
    StructField("id", LongType(), True),
    StructField("type", StringType(), True),
    StructField("namespace", IntegerType(), True),
    StructField("title", StringType(), True),
    StructField("comment", StringType(), True),
    StructField("timestamp", LongType(), True),
    StructField("user", StringType(), True),
    StructField("bot", BooleanType(), True),
    StructField("server_name", StringType(), True),
    StructField("wiki", StringType(), True),
])

def transform_wikimedia_stream(kafka_df: DataFrame) -> DataFrame:
    """
    Parses the JSON data from a Kafka DataFrame and flattens the structure.
    This is a pure, testable transformation function.
    """
    return kafka_df.select(
        from_json(col("value").cast("string"), WIKIMEDIA_SCHEMA).alias("data")
    ).select("data.*")