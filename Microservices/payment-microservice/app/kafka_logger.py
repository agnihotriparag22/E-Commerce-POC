from app.kafka_logger import get_kafka_logger

KAFKA_BROKER = 'localhost:9092'  # Change as needed
KAFKA_TOPIC = 'microservice-logs'  # Change as needed
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

# Example usage:
logger.info('Payment microservice started')
