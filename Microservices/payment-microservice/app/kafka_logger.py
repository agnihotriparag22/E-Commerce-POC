from dotenv import load_dotenv
load_dotenv()
import logging
from confluent_kafka import Producer
import json
from dotenv import load_dotenv
import os

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.payment-service' 

class KafkaLoggingHandler(logging.Handler):
    def __init__(self, kafka_broker, kafka_topic):
        if not kafka_broker:
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS is not set. Cannot connect to Kafka.")
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
    
    handler_exists = any(
        isinstance(h, KafkaLoggingHandler) and getattr(h, 'topic', None) == kafka_topic
        for h in logger.handlers
    )
    if not handler_exists:
        handler = KafkaLoggingHandler(kafka_broker, kafka_topic)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
        logger.addHandler(stream_handler)
    return logger
