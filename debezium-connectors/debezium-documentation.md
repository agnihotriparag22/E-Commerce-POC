# Debezium Documentation for E-Commerce-POC

## Table of Contents
- [What are CDC Operations and Their Importance?](#what-are-cdc-operations-and-their-importance)
- [What is Debezium?](#what-is-debezium)
- [Why Debezium over Kafka Connect?](#why-debezium-over-kafka-connect)
- [How to Create a Debezium User and Implement It](#how-to-create-a-debezium-user-and-implement-it)
- [How to Write a Debezium Connector Config File](#how-to-write-a-debezium-connector-config-file)
- [Debezium Implementation in This Project](#debezium-implementation-in-this-project)

---

## What are CDC Operations and Their Importance?
**Change Data Capture (CDC)** refers to the process of identifying and capturing changes made to data in a database. The main CDC operations are:
- **Insert:** New row added to a table.
- **Update:** Existing row modified.
- **Delete:** Row removed from a table.

**Importance of CDC:**
- **Real-time Data Integration:** Keeps downstream systems (analytics, search, caches) in sync with the source database in real time.
- **Event-Driven Architectures:** Enables microservices to react to data changes as events.
- **Audit and Compliance:** Maintains a history of changes for auditing purposes.
- **Data Replication and Migration:** Facilitates zero-downtime migrations and multi-region replication.

## What is Debezium?
Debezium is an open-source distributed platform for Change Data Capture (CDC). It captures row-level changes in databases (such as inserts, updates, and deletes) and streams them to Apache Kafka topics in real time. This enables downstream applications to react to data changes as they happen, supporting use cases like event-driven architectures, data replication, and real-time analytics.

## Why Debezium over Kafka Connect?
While Kafka Connect is a framework for connecting Kafka with external systems (databases, key-value stores, search indexes, etc.), Debezium is built on top of Kafka Connect and specializes in CDC. Here's why Debezium is preferred for CDC use cases:
- **Purpose-built for CDC:** Debezium provides connectors specifically designed for capturing database changes.
- **Schema Evolution:** Handles schema changes in source databases gracefully.
- **Rich Metadata:** Emits detailed change events, including before/after states and transaction metadata.
- **Community and Ecosystem:** Actively maintained with support for many popular databases (MySQL, PostgreSQL, MongoDB, SQL Server, etc.).


## How to Create a Debezium User and Implement It
To use Debezium, you need a database user with sufficient privileges to read the database's change logs and schema. Here's a general guide for creating a Debezium user (example for MySQL):

```sql
CREATE USER 'debezium'@'%' IDENTIFIED BY 'dbz';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'debezium'@'%';
FLUSH PRIVILEGES;
```

**Implementation Steps:**
1. **Create the user** in your database as shown above.
2. **Configure the Debezium connector** to use this user's credentials.
3. **Deploy the connector** using Kafka Connect REST API or configuration files.

> **Additional MySQL Configuration Required for Debezium:**
>
 To enable Debezium to capture changes, ensure the following MySQL server settings are configured:
>
 - `log_bin` must be **ON** (enables binary logging).
 - `binlog_format` must be set to **ROW** (captures row-level changes).
 - `server_id` must be set (e.g., `server_id=1` for a single instance; must be unique in a cluster).

> Example configuration in your MySQL config file (`my.cnf` or `my.ini`):

```ini
 [mysqld]
 log_bin = ON
 binlog_format = ROW
 server_id = 1
 ```
>
> After updating these settings, restart your MySQL server for the changes to take effect.

If you are using Amazon RDS, you can configure these settings by creating a custom parameter group:

1. In the AWS RDS Console, go to **Parameter groups** and create a new parameter group for your MySQL instance.
2. Set the following parameters in the custom group:
   - `binlog_format` = `ROW`
   - `log_bin` = `ON`
   - `server_id` = (set a unique integer, e.g., `1`)
3. Apply the custom parameter group to your RDS instance and reboot the instance for the changes to take effect.

> **Note:** The exact privileges and commands may vary depending on your database (PostgreSQL, MongoDB, etc.).

## How to Write a Debezium Connector Config File
A Debezium connector config file is a JSON file that specifies how Debezium should connect to your database and what tables to monitor. Here's a sample structure (for MySQL):

```json
{
  "name": "order-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "database.hostname": "localhost", // replace with your actual database endpoint
    "database.port": "3306", // replace with your actual database
    "database.user": "debezium", // replace with your actual database user
    "database.password": "dbz", // replace with your actual database password
    "database.server.id": "184054",
    "database.server.name": "orderdb",
    "database.include.list": "order_db",
    "table.include.list": "order_db.orders",
    "schema.history.internal.kafka.bootstrap.servers": "kafka:9092",
    "schema.history.internal.kafka.topic": "schema-changes.orderdb"
  }
}
```

**Key Fields:**
- `connector.class`: The Debezium connector class for your database.
- `database.*`: Connection details and credentials.
- `database.server.name`: Logical name for the database server (used as a prefix for Kafka topics).
- `database.include.list` / `table.include.list`: Databases/tables to monitor.
- `schema.history.internal.kafka.bootstrap.servers`: Hosted kafka bootstrap server
- `schema.history.internal.kafka.topic`: Kafka topic for schema history.

## Debezium Implementation in This Project
In this E-Commerce-POC, Debezium is used to capture changes from the databases of different microservices (Order, Payment, Product) and stream them to Kafka topics. This enables real-time synchronization and event-driven processing across services.

### Connector Config Files
The following Debezium connector config files are used in this project:

- [`order-db-connector.json`](./order-db-connector.json)
- [`payment-service-db-connector.json`](./payment-service-db-connector.json)
- [`product-service-db-connector.json`](./product-service-db-connector.json)

#### Example: `order-db-connector.json`
```json
{
  "name": "order-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "database.hostname": "localhost",
    "database.port": "3306",
    "database.user": "debezium",
    "database.password": "dbz",
    "database.server.id": "184054",
    "database.server.name": "orderdb",
    "database.include.list": "order_db",
    "table.include.list": "order_db.orders",
    "schema.history.internal.kafka.bootstrap.servers": "kafka:9092",
    "schema.history.internal.kafka.topic": "schema-changes.orderdb"
  }
}
```

> The other connector files follow a similar structure, tailored for their respective databases and tables.

### How It Works in the Project
- Each microservice database (Order, Payment, Product) has a corresponding Debezium connector.
- When a change occurs (insert, update, delete), Debezium captures the event and publishes it to a Kafka topic.
- Microservices or consumers can subscribe to these topics to react to changes in real time (e.g., update caches, trigger workflows, synchronize data).

### Benefits in This Architecture
- **Loose Coupling:** Services communicate via events, not direct API calls.
- **Scalability:** Easily add new consumers or services that react to data changes.
- **Auditability:** All changes are logged as events in Kafka.
- **Resilience:** Decoupled event-driven design improves fault tolerance.

---

## References
- [Debezium Documentation](https://debezium.io/documentation/)
- [Kafka Connect Documentation](https://kafka.apache.org/documentation/#connect)
- [CDC Patterns](https://martinfowler.com/articles/change-data-capture.html) 
