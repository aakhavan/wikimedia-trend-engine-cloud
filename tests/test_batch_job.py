import pytest
from datetime import datetime

# No need for findspark or SparkSession imports here anymore,
# as the fixture handles it.
from pyspark.sql import Row
from src.batch.batch_job import WikimediaBatchJob

# The spark_session fixture is now automatically provided by conftest.py

def test_transform_data(spark_session):
    """
    Tests the core aggregation logic of the batch job.
    We create a sample DataFrame mimicking the raw Iceberg table,
    apply the transformation, and verify the aggregated results.
    """
    # Arrange: Create sample data that looks like the raw stream data
    # We include multiple domains, types, and timestamps to test the grouping and filtering.
    raw_data = [
        Row(meta=Row(dt='2024-07-25T10:05:00Z', domain='en.wikipedia.org'), type='edit'),
        Row(meta=Row(dt='2024-07-25T10:15:00Z', domain='en.wikipedia.org'), type='edit'),
        Row(meta=Row(dt='2024-07-25T10:25:00Z', domain='de.wikipedia.org'), type='edit'),
        Row(meta=Row(dt='2024-07-25T10:35:00Z', domain='en.wikipedia.org'), type='log'),  # Should be filtered out
        Row(meta=Row(dt='2024-07-25T11:05:00Z', domain='fr.wikipedia.org'), type='edit'),
    ]
    raw_df = spark_session.createDataFrame(raw_data)

    # Act: Call the static transformation method on the class
    aggregated_df = WikimediaBatchJob.transform_data(raw_df)
    results = aggregated_df.orderBy("event_hour", "domain").collect()

    # Assert: Check the schema and the aggregated values
    expected_columns = ["event_hour", "domain", "edit_count"]
    assert all(col in aggregated_df.columns for col in expected_columns)
    assert len(results) == 3  # We expect 3 groups (enwiki@10, dewiki@10, frwiki@11)

    # Check the first group: de.wikipedia.org at 10:00
    assert results[0].domain == 'de.wikipedia.org'
    assert results[0].event_hour.replace(tzinfo=None) == datetime(2024, 7, 25, 12, 0, 0)
    assert results[0].edit_count == 1

    # Check the second group: en.wikipedia.org at 10:00
    assert results[1].domain == 'en.wikipedia.org'
    assert results[1].event_hour.replace(tzinfo=None) == datetime(2024, 7, 25, 12, 0, 0)
    assert results[1].edit_count == 2

    # Check the third group: fr.wikipedia.org at 11:00
    assert results[2].domain == 'fr.wikipedia.org'
    assert results[2].event_hour.replace(tzinfo=None) == datetime(2024, 7, 25, 13, 0, 0)
    assert results[2].edit_count == 1