import logging
from confluent_kafka import Producer
import json

class KafkaLoggingHandler(logging.Handler):
    def __init__(self, kafka_broker, kafka_topic):
        super().__init__()
        self.producer = Producer({'bootstrap.servers': kafka_broker})
        self.topic = kafka_topic

    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.producer.produce(self.topic, log_entry.encode('utf-8'))
            self.producer.flush()
        except Exception as e:
            print(f"Failed to send log to Kafka: {e}")

def get_kafka_logger(name, kafka_broker, kafka_topic):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = KafkaLoggingHandler(kafka_broker, kafka_topic)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger
