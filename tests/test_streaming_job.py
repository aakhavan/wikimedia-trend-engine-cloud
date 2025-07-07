import pytest
import sys
from pyspark.sql import SparkSession
# Import the pure function directly
from src.streaming.transformations import transform_wikimedia_stream
import os
import sys
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


@pytest.fixture(scope="session")
def spark_session():
    """
    Creates a robust SparkSession for local testing.

    This fixture explicitly sets the Python executable for the driver and workers
    to be the same one that is running pytest. This prevents common environment
    issues where Spark workers fail to start, especially on Windows.
    """
    python_executable = sys.executable

    return SparkSession.builder \
        .master("local[2]") \
        .appName("WikimediaStreamingTests") \
        .config("spark.pyspark.python", python_executable) \
        .config("spark.pyspark.driver.python", python_executable) \
        .getOrCreate()


def test_transform_stream(spark_session):
    """
    Tests the core transformation logic by calling the pure transformation function.
    """
    # Arrange: Create a sample DataFrame with a JSON string in the 'value' column
    json_string = """
    {
        "meta": {"domain": "en.wikipedia.org", "id": null, "dt": null},
        "id": 12345,
        "type": "edit",
        "namespace": null,
        "title": "Test Title",
        "comment": null,
        "timestamp": null,
        "user": "TestUser",
        "bot": false,
        "server_name": null,
        "wiki": "enwiki"
    }
    """
    source_df = spark_session.createDataFrame([(json_string,)], ["value"])

    # Act: Call the pure function directly.
    transformed_df = transform_wikimedia_stream(source_df)

    # Assert: Check that the schema is correct and the data was parsed properly
    assert "title" in transformed_df.columns
    assert "user" in transformed_df.columns
    assert "bot" in transformed_df.columns

    result = transformed_df.collect()[0]
    assert result.title == "Test Title"
    assert result.user == "TestUser"
    assert result.bot is False
    assert result.meta.domain == "en.wikipedia.org"