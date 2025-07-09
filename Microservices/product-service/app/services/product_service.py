import os
from app.services.product_producer import ProductProducer
from app.repositories.product_repository import ProductRepository
import asyncio
from app.kafka_logger import get_kafka_logger

class ProductService:
    def __init__(self, db):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.producer = ProductProducer()
        KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.logger = get_kafka_logger(__name__, KAFKA_BROKER, "logs.product-service")

    async def update_stock(self, product_id: int, quantity: int, increase: bool = False):
        try:
            if increase:
                product = await self.product_repo.increase_product_stock(product_id, quantity)
                status = "SUCCESSFUL" if product else "FAILED"
            else:
                product, error = await self.product_repo.decrease_product_stock(product_id, quantity)
                status = "SUCCESSFUL" if product else "FAILED"
            await self.producer.send_stock_updated_event(product_id, None, status)
            self.logger.info(f"Stock update event sent for product {product_id}, status={status}")
            return product
        except Exception as e:
            self.logger.error(f"Error updating stock for product {product_id}: {e}", exc_info=True)
            raise
