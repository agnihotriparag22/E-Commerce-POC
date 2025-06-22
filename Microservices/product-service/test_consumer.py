from kafka import KafkaConsumer
import json
import logging

def consume_logs(topic_name, bootstrap_servers='3.145.107.119:9092'):
    
    try:
        # Create Kafka consumer
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='earliest',  # Start from beginning if no offset
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
            value_deserializer=lambda x: x.decode('utf-8') if x else None
        )
        
        print(f"Connected to Kafka. Consuming logs from topic: {topic_name}")
        print("Press Ctrl+C to stop consuming...")
        
        # Consume messages
        for message in consumer:
            try:
                log_data = message.value
                timestamp = message.timestamp
                partition = message.partition
                offset = message.offset
                
                # Print log information
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

# Example usage
if __name__ == "__main__":
    # Replace with your actual topic name and Kafka server details
    TOPIC_NAME = "product-events"
    KAFKA_SERVERS = "3.145.107.119:9092"  # Change to your Kafka broker address
    
    consume_logs(
        topic_name=TOPIC_NAME,
        bootstrap_servers=KAFKA_SERVERS
    )