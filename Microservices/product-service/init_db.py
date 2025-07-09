from sqlalchemy.orm import Session
from app.models.product import Category, Product
from app.db.database import SessionLocal, engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

# Sample data
categories = [
    {
        "name": "Electronics",
        "description": "Electronic devices and gadgets"
    },
    {
        "name": "Clothing",
        "description": "Fashion and apparel items"
    },
    {
        "name": "Books",
        "description": "Books and publications"
    },
    {
        "name": "Home & Kitchen",
        "description": "Home appliances and kitchen items"
    },
    {
        "name": "Sports",
        "description": "Sports equipment and accessories"
    }
]

products = {
    "Electronics": [
        {"name": "Smartphone X", "description": "Latest smartphone with advanced features", "price": 699.99, "stock": 50},
        {"name": "Laptop Pro", "description": "High-performance laptop for professionals", "price": 1299.99, "stock": 30},
        {"name": "Wireless Earbuds", "description": "Premium wireless earbuds with noise cancellation", "price": 149.99, "stock": 100},
        {"name": "Smart Watch", "description": "Fitness tracker and smartwatch", "price": 199.99, "stock": 75},
        {"name": "4K Monitor", "description": "Ultra HD monitor for gaming and work", "price": 399.99, "stock": 40},
        {"name": "Gaming Console", "description": "Next-gen gaming console", "price": 499.99, "stock": 25},
        {"name": "Bluetooth Speaker", "description": "Portable waterproof speaker", "price": 79.99, "stock": 60},
        {"name": "Tablet Pro", "description": "Professional tablet with stylus support", "price": 599.99, "stock": 35},
        {"name": "Camera Kit", "description": "DSLR camera with lens kit", "price": 899.99, "stock": 20},
        {"name": "VR Headset", "description": "Virtual reality gaming headset", "price": 299.99, "stock": 45}
    ],
    "Clothing": [
        {"name": "Men's T-Shirt", "description": "Cotton casual t-shirt", "price": 24.99, "stock": 200},
        {"name": "Women's Dress", "description": "Summer floral dress", "price": 49.99, "stock": 150},
        {"name": "Jeans", "description": "Classic blue denim jeans", "price": 59.99, "stock": 100},
        {"name": "Winter Jacket", "description": "Warm winter jacket", "price": 129.99, "stock": 80},
        {"name": "Running Shoes", "description": "Lightweight running shoes", "price": 89.99, "stock": 120},
        {"name": "Formal Shirt", "description": "Business casual shirt", "price": 39.99, "stock": 90},
        {"name": "Sweater", "description": "Wool blend sweater", "price": 45.99, "stock": 110},
        {"name": "Skirt", "description": "A-line midi skirt", "price": 34.99, "stock": 95},
        {"name": "Hoodie", "description": "Cotton hooded sweatshirt", "price": 54.99, "stock": 85},
        {"name": "Swimwear", "description": "Beach swimsuit", "price": 29.99, "stock": 70}
    ],
    "Books": [
        {"name": "The Great Novel", "description": "Bestselling fiction novel", "price": 19.99, "stock": 100},
        {"name": "Cookbook", "description": "Collection of gourmet recipes", "price": 29.99, "stock": 80},
        {"name": "History Book", "description": "World history encyclopedia", "price": 39.99, "stock": 60},
        {"name": "Science Textbook", "description": "Advanced physics textbook", "price": 89.99, "stock": 40},
        {"name": "Children's Book", "description": "Illustrated storybook", "price": 14.99, "stock": 120},
        {"name": "Biography", "description": "Famous person's life story", "price": 24.99, "stock": 70},
        {"name": "Poetry Collection", "description": "Modern poetry anthology", "price": 17.99, "stock": 90},
        {"name": "Self-Help Book", "description": "Personal development guide", "price": 21.99, "stock": 85},
        {"name": "Art Book", "description": "Famous paintings collection", "price": 49.99, "stock": 50},
        {"name": "Travel Guide", "description": "City travel guide", "price": 19.99, "stock": 75}
    ],
    "Home & Kitchen": [
        {"name": "Coffee Maker", "description": "Programmable coffee machine", "price": 79.99, "stock": 40},
        {"name": "Blender", "description": "High-speed blender", "price": 59.99, "stock": 60},
        {"name": "Toaster", "description": "4-slice toaster", "price": 39.99, "stock": 80},
        {"name": "Cookware Set", "description": "10-piece non-stick cookware set", "price": 149.99, "stock": 30},
        {"name": "Dinnerware Set", "description": "8-piece ceramic dinnerware set", "price": 89.99, "stock": 45},
        {"name": "Vacuum Cleaner", "description": "Cordless vacuum cleaner", "price": 199.99, "stock": 25},
        {"name": "Air Purifier", "description": "HEPA air purifier", "price": 129.99, "stock": 35},
        {"name": "Bedding Set", "description": "Queen size bedding set", "price": 69.99, "stock": 50},
        {"name": "Kitchen Knife Set", "description": "Professional knife set", "price": 119.99, "stock": 40},
        {"name": "Food Processor", "description": "Multi-function food processor", "price": 89.99, "stock": 30}
    ],
    "Sports": [
        {"name": "Yoga Mat", "description": "Non-slip yoga mat", "price": 29.99, "stock": 100},
        {"name": "Dumbbell Set", "description": "Adjustable weight set", "price": 89.99, "stock": 50},
        {"name": "Basketball", "description": "Official size basketball", "price": 24.99, "stock": 80},
        {"name": "Tennis Racket", "description": "Professional tennis racket", "price": 79.99, "stock": 40},
        {"name": "Running Shoes", "description": "Professional running shoes", "price": 99.99, "stock": 60},
        {"name": "Bicycle", "description": "Mountain bike", "price": 299.99, "stock": 20},
        {"name": "Swimming Goggles", "description": "Anti-fog swimming goggles", "price": 19.99, "stock": 90},
        {"name": "Fitness Tracker", "description": "Activity and heart rate monitor", "price": 69.99, "stock": 70},
        {"name": "Camping Tent", "description": "4-person camping tent", "price": 149.99, "stock": 30},
        {"name": "Golf Set", "description": "Complete golf club set", "price": 399.99, "stock": 15}
    ]
}

def init_db():
    db = SessionLocal()
    try:
        # Check if database is already populated
        if db.query(Category).first():
            print("Database already populated!")
            return

        # Create categories
        category_objects = {}
        for category_data in categories:
            category = Category(**category_data)
            db.add(category)
            db.flush()  # Flush to get the ID
            category_objects[category.name] = category

        # Create products
        for category_name, product_list in products.items():
            category = category_objects[category_name]
            for product_data in product_list:
                product = Product(**product_data, category_id=category.id)
                db.add(product)

        db.commit()
        print("Database populated successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 