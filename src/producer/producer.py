import json
import yaml
import logging
import requests
import sseclient
import boto3
from confluent_kafka import Producer
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class WikimediaStreamProducer:
    """
    A class to handle producing Wikimedia stream events to an AWS MSK Kafka cluster
    using the high-performance Confluent-Kafka client.
    """

    def __init__(self, config_path='config/config.yml'):
        self.config = self._load_config(config_path)
        self.producer = self._create_kafka_producer()
        logging.info("WikimediaStreamProducer initialized with Confluent-Kafka client.")

    def _load_config(self, path):
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.error("Configuration file not found at path: %s", path)
            raise

    def _get_msk_bootstrap_servers(self):
        region = self.config['aws']['region']
        try:
            kafka_client = boto3.client('kafka', region_name=region)
            clusters = kafka_client.list_clusters_v2()
            if not clusters['ClusterInfoList']:
                logging.error("No MSK clusters found in region %s.", region)
                raise RuntimeError(f"No MSK clusters found in region {region}.")

            cluster_arn = clusters['ClusterInfoList'][0]['ClusterArn']
            response = kafka_client.get_bootstrap_brokers(ClusterArn=cluster_arn)
            logging.info("Successfully retrieved MSK bootstrap brokers.")
            return response['BootstrapBrokerStringSaslIam']
        except (NoCredentialsError, PartialCredentialsError):
            logging.error("AWS credentials not found. Ensure the EC2 instance has the correct IAM role.")
            raise

    def _create_kafka_producer(self):
        """Creates a Kafka producer using the Confluent-Kafka library."""
        bootstrap_servers = self._get_msk_bootstrap_servers()

        # Configuration for Confluent-Kafka client with IAM
        producer_config = {
            'bootstrap.servers': bootstrap_servers,
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'OAUTHBEARER',
            'sasl.login.callback.handler.class': 'software.amazon.msk.auth.iam.IAMOAuthBearerLoginCallbackHandler'
        }

        # Add performance settings from our config.yml
        # Note: confluent-kafka uses '.' instead of '_' for keys
        for key, value in self.config['kafka']['producer_config'].items():
            producer_config[key.replace('_', '.')] = value

        try:
            producer = Producer(producer_config)
            logging.info("Confluent-Kafka producer created successfully.")
            return producer
        except Exception as e:
            logging.error("Failed to create Confluent-Kafka producer: %s", e)
            raise

    def _delivery_report(self, err, msg):
        """Callback for reporting message delivery status."""
        if err is not None:
            logging.error(f"Message delivery failed: {err}")
        else:
            logging.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def run(self):
        """Connects to the stream and produces events."""
        url = self.config['wikimedia']['stream_url']
        topic_name = self.config['kafka']['topic_name']

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            client = sseclient.SSEClient(response)

            logging.info("Connected to Wikimedia stream. Producing to topic '%s'...", topic_name)
            for event in client.events():
                if event.event == 'message':
                    try:
                        # The produce() method is non-blocking
                        self.producer.produce(
                            topic_name,
                            value=event.data.encode('utf-8'),
                            callback=self._delivery_report
                        )
                        # Poll to allow delivery reports to be served
                        self.producer.poll(0)
                    except BufferError:
                        logging.warning("Local producer queue is full. Flushing...")
                        self.producer.flush()
                    except Exception as e:
                        logging.error(f"An error occurred while producing message: {e}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to connect to Wikimedia stream URL: {e}")
        finally:
            logging.info("Flushing final messages...")
            self.producer.flush()  # Ensure all outstanding messages are sent before exiting


if __name__ == "__main__":
    try:
        producer_app = WikimediaStreamProducer()
        producer_app.run()
    except Exception as e:
        logging.critical(f"Application failed to start. Error: {e}")