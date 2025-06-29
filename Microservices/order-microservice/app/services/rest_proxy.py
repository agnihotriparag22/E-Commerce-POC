import os
import httpx
import logging
from dotenv import load_dotenv
from app.kafka_logger import get_kafka_logger

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = 'logs.order-service'  
logger = get_kafka_logger(__name__, KAFKA_BROKER, KAFKA_TOPIC)


# Load environment variables
load_dotenv()

class RestProxyService:
    def __init__(self, topic: str = None):
        # Load environment variables in the constructor
        self.base_url = os.getenv("KAFKA_REST_PROXY_URL")
        self.topic = topic or os.getenv("KAFKA_TOPIC", "order-events")
        
        # Validate that the base_url is set and has proper protocol
        if not self.base_url:
            raise ValueError("KAFKA_REST_PROXY_URL environment variable is not set")
        
        # Ensure the URL has proper protocol
        if not self.base_url.startswith(('http://', 'https://')):
            logger.warning(f"Adding http:// protocol to Kafka REST Proxy URL: {self.base_url}")
            self.base_url = f"http://{self.base_url}"
        
        logger.info(f"RestProxyService initialized with URL: {self.base_url}, Topic: {self.topic}")

    async def send_event(self, value: dict, key: str = None, auth_token: str = None, topic: str = None):
        headers = {"Content-Type": "application/vnd.kafka.json.v2+json"}
        
        # Add authorization header if token is provided
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        payload = {
            "records": [
                {"value": value} if not key else {"key": key, "value": value}
            ]
        }
        
        use_topic = topic or self.topic
        url = f"{self.base_url}/topics/{use_topic}"
        logger.debug(f"Sending event to URL: {url}")
        logger.debug(f"Payload: {payload}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Successfully sent event to Kafka REST Proxy: {value} (topic: {use_topic})")
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Request error sending event to Kafka REST Proxy: {e}")
                logger.error(f"URL attempted: {url}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error sending event to Kafka REST Proxy: {e}")
                logger.error(f"Response: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Failed to send event to Kafka REST Proxy: {e}")
                logger.error(f"URL attempted: {url}")
                raise