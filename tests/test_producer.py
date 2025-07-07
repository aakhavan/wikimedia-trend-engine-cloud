import pytest
from unittest.mock import patch, MagicMock
from src.producer.producer import WikimediaStreamProducer

# Use pytest's 'mocker' fixture for easy mocking
def test_producer_initialization(mocker):
    """
    Tests that the producer class initializes correctly by loading the config.
    We mock _create_kafka_producer to prevent it from trying to connect to AWS.
    """
    # Mock the methods that have external dependencies
    mocker.patch.object(WikimediaStreamProducer, '_create_kafka_producer', return_value=MagicMock())
    mocker.patch("builtins.open", mocker.mock_open(read_data="""
aws:
  region: 'eu-central-1'
"""))

    producer_app = WikimediaStreamProducer(config_path='dummy/path.yml')
    assert producer_app.config['aws']['region'] == 'eu-central-1'
    # Assert that our mock was called, confirming __init__ tried to create a producer
    WikimediaStreamProducer._create_kafka_producer.assert_called_once()


@patch('src.producer.producer.boto3.client')
@patch('src.producer.producer.Producer')  # <-- CORRECTED: Patch the new Producer class
def test_create_kafka_producer(MockConfluentProducer, mock_boto_client):
    """
    Tests the logic for creating a Confluent-Kafka producer.
    We mock the AWS and Kafka clients to verify our code calls them with the correct IAM config.
    """
    # Arrange: Configure the mock AWS client
    mock_kafka_client = MagicMock()
    mock_kafka_client.list_clusters_v2.return_value = {'ClusterInfoList': [{'ClusterArn': 'dummy_arn'}]}
    mock_kafka_client.get_bootstrap_brokers.return_value = {'BootstrapBrokerStringSaslIam': 'dummy_brokers'}
    mock_boto_client.return_value = mock_kafka_client

    # Instantiate our class, but we will call the "private" method directly
    producer_app = WikimediaStreamProducer.__new__(WikimediaStreamProducer)
    producer_app.config = {
        'aws': {'region': 'eu-central-1'},
        'kafka': {'producer_config': {'acks': 'all', 'linger.ms': 5}}
    }

    # Act: Call the method we want to test
    producer_instance = producer_app._create_kafka_producer()

    # Assert: Check that the Confluent Producer was called with the expected IAM dictionary
    mock_boto_client.assert_called_with('kafka', region_name='eu-central-1')
    expected_config = {
        'bootstrap.servers': 'dummy_brokers',
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'OAUTHBEARER',
        'sasl.login.callback.handler.class': 'software.amazon.msk.auth.iam.IAMOAuthBearerLoginCallbackHandler',
        'acks': 'all',
        'linger.ms': 5
    }
    MockConfluentProducer.assert_called_once_with(expected_config)
    assert producer_instance is not None