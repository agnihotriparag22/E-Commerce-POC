import os
import httpx
from app.kafka_logger import get_kafka_logger

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.product-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)

SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")

class SchemaRegistryService:
    def __init__(self, subject: str):
        self.subject = subject
        self.base_url = SCHEMA_REGISTRY_URL
        
    async def register_schema(self, schema: dict):
        url = f"{self.base_url}/subjects/{self.subject}/versions"
        headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
        payload = {"schema": schema}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Registered schema for subject {self.subject}")
                return response.json()
            except Exception as e:
                logger.error(f"Failed to register schema: {e}")
                raise

    async def get_latest_schema(self):
        url = f"{self.base_url}/subjects/{self.subject}/versions/latest"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to fetch latest schema: {e}")
                raise 