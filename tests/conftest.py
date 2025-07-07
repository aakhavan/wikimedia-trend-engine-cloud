import pytest
import findspark
import sys

# This initialization runs once before any tests are collected
findspark.init()

from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark_session():
    """
    This is the central, shared SparkSession for all tests.
    It is configured for robust local testing:
    - Uses findspark to locate the Spark installation.
    - Sets the timezone to UTC to prevent timezone-related errors.
    - Explicitly sets the Python executable for Spark workers.
    """
    python_executable = sys.executable

    return SparkSession.builder \
        .master("local[2]") \
        .appName("WikimediaProjectTests") \
        .config("spark.sql.session.timeZone", "UTC") \
        .config("spark.pyspark.python", python_executable) \
        .config("spark.pyspark.driver.python", python_executable) \
        .getOrCreate()