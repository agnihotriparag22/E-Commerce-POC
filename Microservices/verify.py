from kafka import KafkaConsumer
import json

# Create consumer
consumer = KafkaConsumer(
    'product-events',  # Topic name
    bootstrap_servers=['3.133.86.124:9092'],
    group_id='product-service',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset="earliest"
)

print("Starting consumer...")

# Consume messages
for message in consumer:
    print(f"Received: {message.value}")