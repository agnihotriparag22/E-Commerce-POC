from locust import HttpUser, task, between
import random
import requests

# Static user data from user-service/init_db.py
USERS = [
    {"username": "admin", "email": "admin@example.com", "password": "admin123", "is_admin": True},
    {"username": "prakhar", "email": "prakhar@example.com", "password": "prakhar123", "is_admin": False},
    {"username": "hrishab", "email": "hrishab@example.com", "password": "hrishab123", "is_admin": False},
    {"username": "parag", "email": "parag@example.com", "password": "parag123", "is_admin": False}
]

PRODUCT_SERVICE_URL = "http://localhost:8002/api/v1/products"
ORDER_SERVICE_URL = "http://localhost:8000/api/v1/orders"
USER_SERVICE_LOGIN_URL = "http://localhost:8001/api/v1/login"

class ECommerceUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Pick a random user and log in
        self.user = random.choice(USERS)
        login_payload = {"email": self.user["email"], "password": self.user["password"]}
        with self.client.post(USER_SERVICE_LOGIN_URL, json=login_payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
            else:
                response.failure(f"Login failed for {self.user['email']}: {response.text}")
                self.token = None
                self.user_id = None
                self.headers = {}

    @task
    def place_order(self):
        if not self.token:
            # Try to log in again
            self.on_start()
            if not self.token:
                return
        # Fetch products
        with self.client.get(PRODUCT_SERVICE_URL, headers=self.headers, name="/api/v1/products") as resp:
            if resp.status_code != 200:
                resp.failure(f"Failed to fetch products: {resp.text}")
                return
            products_data = resp.json().get("products", [])
            if not products_data:
                resp.failure("No products available")
                return
        # Pick random products and quantities
        num_items = random.randint(1, min(5, len(products_data)))
        items = []
        chosen_products = random.sample(products_data, num_items)
        total_amount = 0.0
        for product in chosen_products:
            quantity = random.randint(1, min(3, product.get("stock", 1)))
            items.append({"product_id": product["id"], "quantity": quantity})
            total_amount += product["price"] * quantity
        # Prepare payment info
        payment_info = {
            "amount": total_amount,
            "card_holder_name": self.user["username"],
            "card_number": "4111111111111111",
            "cvv": "123",
            "expiry_date": "12/25"
        }
        order_payload = {
            "user_id": self.user_id,
            "items": items,
            "payment_info": payment_info
        }
        # Place order
        with self.client.post(ORDER_SERVICE_URL, json=order_payload, headers=self.headers, name="/api/v1/orders") as order_resp:
            if order_resp.status_code == 201:
                order_resp.success()
            else:
                order_resp.failure(f"Order failed: {order_resp.text}") 
                
                
#Command to run the load test:
# locust -f load_test.py --host 8001