from kafka import KafkaConsumer
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def consume_logs(topic_name, bootstrap_servers=None):
    if bootstrap_servers is None:
        bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    
    try:
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='earliest', 
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
            value_deserializer=lambda x: x.decode('utf-8') if x else None
        )
        
        print(f"Connected to Kafka server: {bootstrap_servers}")
        print(f"Consuming logs from topic: {topic_name}")
        print("Press Ctrl+C to stop consuming...")
        
        for message in consumer:
            try:
                log_data = message.value
                timestamp = datetime.fromtimestamp(message.timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                partition = message.partition
                offset = message.offset
                
                
                print(f"[{timestamp}] Partition: {partition}, Offset: {offset}")
                print(f"Log: {log_data}")
                print("-" * 50)
                
            except Exception as e:
                print(f"Error processing message: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\nStopping consumer...")
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
    finally:
        if 'consumer' in locals():
            consumer.close()
            print("Consumer closed.")


if __name__ == "__main__":
    TOPIC_NAME = os.getenv('KAFKA_TOPIC_CDC', 'productservicedb.product_service_db.products')
    
    consume_logs(topic_name=TOPIC_NAME)