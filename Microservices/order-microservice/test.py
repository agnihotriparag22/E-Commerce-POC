import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.services.rest_proxy import RestProxyService
from app.schemas.schema_registry import SchemaRegistryService

async def test_rest_proxy():
    rest_proxy = RestProxyService()
    event = {
        "event": "test_event",
        "order_id": 123,
        "user_id": 1,
        "product_id": 2,
        "quantity": 5
    }
    result = await rest_proxy.send_event(event)
    print("REST Proxy send result:", result)

async def test_schema_registry():
    schema_registry = SchemaRegistryService(subject="order-events-value")
    schema = '{"type": "record", "name": "OrderEvent", "fields": [{"name": "event", "type": "string"}, {"name": "order_id", "type": "int"}]}'
    # Register schema
    result = await schema_registry.register_schema(schema)
    print("Schema Registry register result:", result)
    # Fetch latest schema
    latest = await schema_registry.get_latest_schema()
    print("Schema Registry latest schema:", latest)

if __name__ == "__main__":
    asyncio.run(test_rest_proxy())
    asyncio.run(test_schema_registry())
    
    
