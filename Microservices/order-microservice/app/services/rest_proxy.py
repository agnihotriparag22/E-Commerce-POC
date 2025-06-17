import os
import httpx
import logging

KAFKA_REST_PROXY_URL = os.getenv("KAFKA_REST_PROXY_URL")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "order-events")

class RestProxyService:
    def __init__(self, topic: str = KAFKA_TOPIC):
        self.topic = topic
        self.base_url = KAFKA_REST_PROXY_URL

    async def send_event(self, value: dict, key: str = None):
        headers = {"Content-Type": "application/vnd.kafka.json.v2+json"}
        payload = {
            "records": [
                {"value": value} if not key else {"key": key, "value": value}
            ]
        }
        url = f"{self.base_url}/topics/{self.topic}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logging.info(f"Sent event to Kafka REST Proxy: {value}")
                return response.json()
            except Exception as e:
                logging.error(f"Failed to send event to Kafka REST Proxy: {e}")
                raise
