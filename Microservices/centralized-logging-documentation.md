# Centralized Logging Documentation for E-Commerce-POC

## Table of Contents
- [What is Centralized Logging?](#what-is-centralized-logging)
- [Why Do We Do Centralized Logging?](#why-do-we-do-centralized-logging)
- [Benefits of Centralized Logging in Microservice Architecture](#benefits-of-centralized-logging-in-microservice-architecture)
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

## Centralized Logging Implementation in This Project
In this E-Commerce-POC, centralized logging is implemented using a custom `kafka_logger` module in all four microservices:
- Order Microservice
- Payment Microservice
- Product Microservice
- User Service

### How It Works
- Each microservice imports and uses the `kafka_logger` module.
- Application logs (info, error, debug, etc.) are sent as messages to a Kafka topic dedicated for logs.
- A centralized log consumer (not shown here, but can be implemented) can subscribe to this Kafka topic to aggregate, store, and analyze logs (e.g., using ELK stack, Grafana Loki, or custom dashboards).

### Example Usage
In each microservice, you will find a file like `kafka_logger.py` (e.g., `Microservices/order-microservice/app/kafka_logger.py`). This module is responsible for producing log messages to Kafka.

**Sample log sending code:**
```python
from kafka_logger import log_info, log_error

log_info('Order created successfully', extra={"order_id": 123})
log_error('Payment failed', extra={"order_id": 123, "reason": "Insufficient funds"})
```

### Benefits in This Project
- **Consistent Logging:** All services use the same logging mechanism and format.
- **Real-Time Log Aggregation:** Logs are available in real time for monitoring and alerting.
- **Easier Debugging:** Developers and operators can trace issues across services using centralized logs.
- **Extensible:** The logging pipeline can be extended to integrate with log storage, visualization, and alerting tools.

---

## References
- [Centralized Logging Concepts](https://martinfowler.com/articles/logging.html)
- [Kafka as a Log Aggregation Solution](https://www.confluent.io/blog/kafka-as-central-log-aggregation-solution/)
- [ELK Stack for Centralized Logging](https://www.elastic.co/what-is/elk-stack) 