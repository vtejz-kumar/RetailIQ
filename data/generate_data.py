import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

STORES = [
    {"name": "RetailIQ Hyderabad", "city": "Hyderabad", "region": "Telangana"},
    {"name": "RetailIQ Vijayawada", "city": "Vijayawada", "region": "Andhra Pradesh"},
    {"name": "RetailIQ Visakhapatnam", "city": "Visakhapatnam", "region": "Andhra Pradesh"},
    {"name": "RetailIQ Bengaluru", "city": "Bengaluru", "region": "Karnataka"},
    {"name": "RetailIQ Chennai", "city": "Chennai", "region": "Tamil Nadu"},
    {"name": "RetailIQ Pune", "city": "Pune", "region": "Maharashtra"},
]

CATEGORIES = [
    "Electronics",
    "Mobile Accessories",
    "Computing",
    "Home Appliances",
    "Office Supplies",
    "Personal Care",
    "Accessories",
]

PRODUCTS = [
    # Electronics
    {"name": "Wireless Headphones", "category": "Electronics", "price": 2999, "cost": 1500, "reorder": 15, "target": 50},
    {"name": "Bluetooth Speaker", "category": "Electronics", "price": 1999, "cost": 900, "reorder": 10, "target": 40},
    {"name": "Smart Watch", "category": "Electronics", "price": 4999, "cost": 2500, "reorder": 8, "target": 30},
    {"name": "Power Bank 20000mAh", "category": "Electronics", "price": 1499, "cost": 700, "reorder": 12, "target": 40},
    {"name": "USB-C Hub", "category": "Electronics", "price": 1299, "cost": 600, "reorder": 10, "target": 35},
    {"name": "Wireless Charger", "category": "Electronics", "price": 899, "cost": 400, "reorder": 15, "target": 45},
    {"name": "Portable SSD 1TB", "category": "Electronics", "price": 7999, "cost": 4500, "reorder": 5, "target": 20},
    {"name": "Action Camera", "category": "Electronics", "price": 15999, "cost": 9000, "reorder": 3, "target": 15},

    # Mobile Accessories
    {"name": "Phone Case Premium", "category": "Mobile Accessories", "price": 599, "cost": 150, "reorder": 20, "target": 80},
    {"name": "Screen Protector Glass", "category": "Mobile Accessories", "price": 299, "cost": 80, "reorder": 25, "target": 100},
    {"name": "Wireless Earbuds", "category": "Mobile Accessories", "price": 2499, "cost": 1200, "reorder": 12, "target": 40},
    {"name": "Car Mount Holder", "category": "Mobile Accessories", "price": 399, "cost": 120, "reorder": 15, "target": 50},
    {"name": "Lightning Cable 2m", "category": "Mobile Accessories", "price": 499, "cost": 150, "reorder": 20, "target": 60},
    {"name": "USB-C Cable 1m", "category": "Mobile Accessories", "price": 299, "cost": 80, "reorder": 25, "target": 80},
    {"name": "Mobile Gimbal", "category": "Mobile Accessories", "price": 4999, "cost": 2800, "reorder": 5, "target": 20},
    {"name": "Ring Light Phone", "category": "Mobile Accessories", "price": 799, "cost": 300, "reorder": 10, "target": 35},

    # Computing
    {"name": "Mechanical Keyboard", "category": "Computing", "price": 3999, "cost": 2000, "reorder": 8, "target": 30},
    {"name": "Gaming Mouse RGB", "category": "Computing", "price": 1799, "cost": 800, "reorder": 10, "target": 35},
    {"name": "Monitor 27inch 144Hz", "category": "Computing", "price": 18999, "cost": 11000, "reorder": 3, "target": 15},
    {"name": "Laptop Stand Aluminum", "category": "Computing", "price": 1299, "cost": 500, "reorder": 12, "target": 40},
    {"name": "Webcam 1080p", "category": "Computing", "price": 2499, "cost": 1200, "reorder": 8, "target": 30},
    {"name": "External HDD 2TB", "category": "Computing", "price": 5499, "cost": 3200, "reorder": 6, "target": 25},
    {"name": "WiFi 6 Router", "category": "Computing", "price": 4999, "cost": 2800, "reorder": 5, "target": 20},
    {"name": "USB Microphone", "category": "Computing", "price": 3499, "cost": 1800, "reorder": 7, "target": 25},

    # Home Appliances
    {"name": "Air Fryer 4L", "category": "Home Appliances", "price": 4999, "cost": 2800, "reorder": 6, "target": 25},
    {"name": "Robot Vacuum", "category": "Home Appliances", "price": 19999, "cost": 12000, "reorder": 3, "target": 12},
    {"name": "Electric Kettle 1.5L", "category": "Home Appliances", "price": 1299, "cost": 550, "reorder": 15, "target": 50},
    {"name": "Hand Blender", "category": "Home Appliances", "price": 1799, "cost": 800, "reorder": 10, "target": 35},
    {"name": "Toaster 4-Slice", "category": "Home Appliances", "price": 2499, "cost": 1200, "reorder": 8, "target": 30},
    {"name": "Coffee Maker", "category": "Home Appliances", "price": 3999, "cost": 2200, "reorder": 7, "target": 25},
    {"name": "Hair Dryer Ionic", "category": "Home Appliances", "price": 1999, "cost": 900, "reorder": 10, "target": 35},
    {"name": "Stand Mixer", "category": "Home Appliances", "price": 8999, "cost": 5000, "reorder": 4, "target": 15},

    # Office Supplies
    {"name": "Ergonomic Chair", "category": "Office Supplies", "price": 12999, "cost": 7500, "reorder": 3, "target": 12},
    {"name": "Standing Desk", "category": "Office Supplies", "price": 18999, "cost": 11000, "reorder": 2, "target": 10},
    {"name": "Monitor Arm", "category": "Office Supplies", "price": 2999, "cost": 1400, "reorder": 8, "target": 30},
    {"name": "Desk Lamp LED", "category": "Office Supplies", "price": 1499, "cost": 650, "reorder": 12, "target": 40},
    {"name": "Wireless Keyboard Mouse", "category": "Office Supplies", "price": 2299, "cost": 1100, "reorder": 10, "target": 35},
    {"name": "Document Scanner", "category": "Office Supplies", "price": 8999, "cost": 5000, "reorder": 4, "target": 15},
    {"name": "Whiteboard 4x3ft", "category": "Office Supplies", "price": 3499, "cost": 1800, "reorder": 6, "target": 25},
    {"name": "Cable Management Kit", "category": "Office Supplies", "price": 599, "cost": 200, "reorder": 15, "target": 50},

    # Personal Care
    {"name": "Electric Toothbrush", "category": "Personal Care", "price": 2499, "cost": 1200, "reorder": 10, "target": 35},
    {"name": "Beard Trimmer", "category": "Personal Care", "price": 1799, "cost": 800, "reorder": 12, "target": 40},
    {"name": "Hair Straightener", "category": "Personal Care", "price": 1999, "cost": 900, "reorder": 10, "target": 35},
    {"name": "Facial Cleansing Brush", "category": "Personal Care", "price": 1299, "cost": 550, "reorder": 15, "target": 50},
    {"name": "Massage Gun", "category": "Personal Care", "price": 4999, "cost": 2800, "reorder": 6, "target": 25},
    {"name": "Nail Care Kit", "category": "Personal Care", "price": 799, "cost": 300, "reorder": 20, "target": 60},
    {"name": "Water Flosser", "category": "Personal Care", "price": 3499, "cost": 1800, "reorder": 8, "target": 30},
    {"name": "Epilator", "category": "Personal Care", "price": 3999, "cost": 2200, "reorder": 7, "target": 25},

    # Accessories
    {"name": "Backpack Laptop 15inch", "category": "Accessories", "price": 2499, "cost": 1200, "reorder": 10, "target": 35},
    {"name": "Wallet Leather RFID", "category": "Accessories", "price": 1299, "cost": 550, "reorder": 15, "target": 50},
    {"name": "Watch Strap Silicone", "category": "Accessories", "price": 499, "cost": 150, "reorder": 20, "target": 70},
    {"name": "Sunglasses Polarized", "category": "Accessories", "price": 1999, "cost": 900, "reorder": 10, "target": 35},
    {"name": "Travel Organizer", "category": "Accessories", "price": 899, "cost": 350, "reorder": 15, "target": 50},
    {"name": "Key Organizer", "category": "Accessories", "price": 599, "cost": 200, "reorder": 20, "target": 60},
    {"name": "Pen Premium Metal", "category": "Accessories", "price": 899, "cost": 350, "reorder": 15, "target": 50},
    {"name": "Card Holder Minimal", "category": "Accessories", "price": 699, "cost": 250, "reorder": 18, "target": 55},
]


def generate_stores_csv():
    path = Path("data/stores.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "city", "region"])
        writer.writeheader()
        for i, store in enumerate(STORES, 1):
            writer.writerow({"id": i, **store})
    print(f"Generated {path} with {len(STORES)} stores")


def generate_products_csv():
    path = Path("data/products.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "category", "price", "cost", "reorder_threshold", "target_stock"])
        writer.writeheader()
        for i, product in enumerate(PRODUCTS, 1):
            row = {
                "id": i,
                "name": product["name"],
                "category": product["category"],
                "price": product["price"],
                "cost": product["cost"],
                "reorder_threshold": product["reorder"],
                "target_stock": product["target"]
            }
            writer.writerow(row)
    print(f"Generated {path} with {len(PRODUCTS)} products")


def generate_sales_and_inventory_csv():
    sales_path = Path("data/sales.csv")
    inventory_path = Path("data/inventory.csv")

    num_days = 90
    end_date = datetime(2025, 8, 31)
    start_date = end_date - timedelta(days=num_days - 1)
    dates = [start_date + timedelta(days=i) for i in range(num_days)]

    num_stores = len(STORES)
    num_products = len(PRODUCTS)

    # Base daily demand per product (varies by product)
    base_demand = {}
    for pid in range(1, num_products + 1):
        base_demand[pid] = random.uniform(0.5, 8.0)

    # Store multipliers (some stores perform better)
    store_multiplier = {
        1: 1.2,   # Hyderabad - strong
        2: 1.0,   # Vijayawada - average
        3: 0.9,   # Visakhapatnam - slightly weak
        4: 1.3,   # Bengaluru - strongest
        5: 0.85,  # Chennai - weak
        6: 1.1,   # Pune - good
    }

    # Category seasonality
    category_trend = {
        "Electronics": 1.0,
        "Mobile Accessories": 1.0,
        "Computing": 1.0,
        "Home Appliances": 1.1,  # slight upward
        "Office Supplies": 0.95,  # slight downward
        "Personal Care": 1.0,
        "Accessories": 1.0,
    }

    # Specific demo scenarios:
    # Product 1 (Wireless Headphones) - stock-out risk at Hyderabad (store 1)
    # Product 2 (Bluetooth Speaker) - overstocked at Chennai (store 5)
    # Product 3 (Smart Watch) - sales spike at Bengaluru (store 4) in last 14 days
    # Product 4 (Power Bank) - sales drop at Vijayawada (store 2) in last 14 days
    # Product 5 (USB-C Hub) - top performer overall
    # Product 6 (Wireless Charger) - poor performer
    # Product 7 (Portable SSD) - zero recent sales at Visakhapatnam (store 3)
    # Product 9 (Phone Case) - strong history for trend analysis

    # Track inventory for each store/product
    current_stock = {}
    for store_id in range(1, num_stores + 1):
        for product_id in range(1, num_products + 1):
            current_stock[(store_id, product_id)] = random.randint(20, 80)

    # Adjust specific scenarios
    # Stock-out risk: Wireless Headphones at Hyderabad - low stock, high sales
    current_stock[(1, 1)] = 12
    # Overstock: Bluetooth Speaker at Chennai - high stock, low sales
    current_stock[(5, 2)] = 120
    # Zero recent sales: Portable SSD at Visakhapatnam
    current_stock[(3, 7)] = 45

    with open(sales_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "date", "store_id", "product_id", "quantity", "revenue"])
        writer.writeheader()

        sale_id = 1
        for date in dates:
            date_str = date.strftime("%Y-%m-%d")
            day_of_year = date.timetuple().tm_yday
            weekend_boost = 1.3 if date.weekday() >= 5 else 1.0

            for store_id in range(1, num_stores + 1):
                for product_id in range(1, num_products + 1):
                    product = PRODUCTS[product_id - 1]
                    category = product["category"]

                    # Calculate demand
                    demand = base_demand[product_id] * store_multiplier[store_id] * category_trend.get(category, 1.0) * weekend_boost

                    # Apply specific scenarios
                    if product_id == 1 and store_id == 1:
                        # High sales for stock-out risk product
                        demand *= 2.5
                    elif product_id == 2 and store_id == 5:
                        # Low sales for overstock product
                        demand *= 0.15
                    elif product_id == 3 and store_id == 4 and day_of_year >= (end_date.timetuple().tm_yday - 13):
                        # Sales spike for Smart Watch at Bengaluru in last 14 days
                        demand *= 3.5
                    elif product_id == 4 and store_id == 2 and day_of_year >= (end_date.timetuple().tm_yday - 13):
                        # Sales drop for Power Bank at Vijayawada in last 14 days
                        demand *= 0.2
                    elif product_id == 5:
                        # Top performer
                        demand *= 1.8
                    elif product_id == 6:
                        # Poor performer
                        demand *= 0.3
                    elif product_id == 7 and store_id == 3 and day_of_year >= (end_date.timetuple().tm_yday - 13):
                        # Zero recent sales for Portable SSD at Visakhapatnam
                        demand = 0

                    # Add noise
                    quantity = max(0, int(random.normalvariate(demand, demand * 0.3)))
                    if quantity > 0:
                        revenue = quantity * product["price"]
                        writer.writerow({
                            "id": sale_id,
                            "date": date_str,
                            "store_id": store_id,
                            "product_id": product_id,
                            "quantity": quantity,
                            "revenue": round(revenue, 2)
                        })
                        sale_id += 1
                        current_stock[(store_id, product_id)] = max(0, current_stock[(store_id, product_id)] - quantity)

    # Final inventory snapshot
    snapshot_date = end_date.strftime("%Y-%m-%d")
    with open(inventory_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "snapshot_date", "store_id", "product_id", "stock_quantity"])
        writer.writeheader()
        inv_id = 1
        for store_id in range(1, num_stores + 1):
            for product_id in range(1, num_products + 1):
                stock = current_stock.get((store_id, product_id), random.randint(10, 60))
                # Ensure specific scenarios are preserved
                if (store_id, product_id) == (1, 1):
                    stock = 12  # Stock-out risk
                elif (store_id, product_id) == (5, 2):
                    stock = 120  # Overstock
                elif (store_id, product_id) == (3, 7):
                    stock = 45  # Zero recent sales
                writer.writerow({
                    "id": inv_id,
                    "snapshot_date": snapshot_date,
                    "store_id": store_id,
                    "product_id": product_id,
                    "stock_quantity": stock
                })
                inv_id += 1

    print(f"Generated {sales_path} with {sale_id - 1} sales records")
    print(f"Generated {inventory_path} with {inv_id - 1} inventory records")


def main():
    Path("data").mkdir(exist_ok=True)
    generate_stores_csv()
    generate_products_csv()
    generate_sales_and_inventory_csv()
    print("\nAll data generated successfully!")


if __name__ == "__main__":
    main()