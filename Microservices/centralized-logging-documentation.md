# Centralized Logging Documentation for E-Commerce-POC

## Table of Contents
- [What is Centralized Logging?](#what-is-centralized-logging)
- [Why Do We Do Centralized Logging?](#why-do-we-do-centralized-logging)
- [Benefits of Centralized Logging in Microservice Architecture](#benefits-of-centralized-logging-in-microservice-architecture)
- [Kafka Topic Strategy for Logging](#kafka-topic-strategy-for-logging)
- [Centralized Logging Implementation in This Project](#centralized-logging-implementation-in-this-project)

---

## What is Centralized Logging?
Centralized logging is the practice of aggregating logs from multiple sources (applications, services, servers) into a single, unified system. Instead of each service or server storing logs locally, all logs are sent to a central location where they can be stored, searched, analyzed, and visualized.

## Why Do We Do Centralized Logging?
- **Unified View:** Provides a single place to view and analyze logs from all services and components.
- **Troubleshooting:** Makes it easier to trace issues that span multiple services or servers.
- **Compliance & Auditing:** Ensures logs are retained and accessible for audits or compliance requirements.
- **Alerting & Monitoring:** Enables real-time alerting and monitoring based on log data.

## Benefits of Centralized Logging in Microservice Architecture
- **End-to-End Visibility:** In a microservices architecture, requests often traverse multiple services. Centralized logging allows you to trace a request across all services, making debugging and monitoring much easier.
- **Correlation:** Logs from different services can be correlated using request IDs or trace IDs, helping to reconstruct the full path of a transaction.
- **Scalability:** As the number of services grows, centralized logging scales to handle logs from all sources without manual intervention.
- **Reduced Operational Overhead:** No need to SSH into individual servers or containers to access logs.
- **Advanced Analytics:** Centralized systems often support querying, visualization, and alerting, enabling deeper insights into system behavior and performance.

## Kafka Topic Strategy for Logging
When designing centralized logging with Kafka, you must decide whether to use a **single topic for all microservices** or **one topic per microservice**. Each approach has its own trade-offs:

### Single Topic for All Microservices
**Pros:**
- **Simplicity:** Easier to manage and configure, especially for small to medium-sized systems.
- **Unified Log Stream:** All logs are in one place, making it easy to search and correlate events across services.
- **Lower Overhead:** Fewer topics to manage in Kafka.

**Cons:**
- **Potential for High Volume:** Large systems may generate a high volume of logs, making the topic harder to manage and scale.
- **Filtering Required:** Consumers must filter logs by service, which may add processing overhead.
- **Retention Policies:** Uniform retention and partitioning may not suit all services.

### One Topic per Microservice
**Pros:**
- **Isolation:** Each service's logs are separated, making it easier to manage, scale, and apply service-specific retention policies.
- **Fine-Grained Control:** You can tune partitions, retention, and access control per service.
- **Easier Scaling:** High-volume services can have more partitions or different configurations.

**Cons:**
- **Increased Complexity:** More topics to manage and monitor.
- **Cross-Service Correlation:** Requires aggregating logs from multiple topics for end-to-end tracing.

### Which to Choose?
- For **smaller systems** or when you want a quick, unified view, a single topic is often sufficient.
- For **larger systems** or when services have very different logging needs, one topic per microservice is recommended.
- You can also use a hybrid approach: a single topic for most logs, and dedicated topics for high-volume or sensitive services.

## Centralized Logging Implementation in This Project
In this E-Commerce-POC, centralized logging is implemented using a custom **kafka_logger utility** (not a module) included in every microservice:
- Order Microservice
- Payment Microservice
- Product Microservice
- User Service

### How It Works
- Each microservice includes the `kafka_logger.py` utility.
- The logger is initialized in the application as follows:
  ```python
  logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)
  ```
- Application code then uses standard logging methods:
  ```python
  logger.info('Order created successfully', extra={"order_id": 123})
  logger.error('Payment failed', extra={"order_id": 123, "reason": "Insufficient funds"})
  ```
- The utility sends log messages to the configured Kafka topic, which can be a single topic for all services or a dedicated topic per service, depending on your chosen strategy.

### kafka_logger Utility Code
Below is the code for the `kafka_logger.py` utility used in each microservice:

```python
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
```

### Example Usage in a Microservice
```python
from kafka_logger import get_kafka_logger

KAFKA_BROKER = 'localhost:9092'  # or your Kafka broker address
KAFKA_TOPIC = 'central-logs'     # or a service-specific topic

logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

logger.info('Order created successfully', extra={"order_id": 123})
logger.error('Payment failed', extra={"order_id": 123, "reason": "Insufficient funds"})
```

### Benefits in This Project
- **Consistent Logging:** All services use the same logging utility and format.
- **Real-Time Log Aggregation:** Logs are available in real time for monitoring and alerting.
- **Easier Debugging:** Developers and operators can trace issues across services using centralized logs.
- **Extensible:** The logging pipeline can be extended to integrate with log storage, visualization, and alerting tools.
- **Flexible Topic Strategy:** You can choose between a single topic or multiple topics for log aggregation, depending on your needs.

---

## References
- [Centralized Logging Concepts](https://martinfowler.com/articles/logging.html)
- [Kafka as a Log Aggregation Solution](https://www.confluent.io/blog/kafka-as-central-log-aggregation-solution/)
- [ELK Stack for Centralized Logging](https://www.elastic.co/what-is/elk-stack) 