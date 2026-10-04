import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "report.db"

customers = [
    "Anu",
    "Rahul",
    "Meena",
    "Priya",
    "Arjun",
    "Karthik",
    "Divya",
    "Naveen"
]

products = [
    "Laptop Stand",
    "Wireless Mouse",
    "Keyboard",
    "USB Hub",
    "Webcam",
    "Headphones"
]

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT NOT NULL,
    product TEXT NOT NULL,
    amount REAL NOT NULL,
    created_at TEXT NOT NULL
)
""")

cursor.execute("DELETE FROM orders")

now = datetime.now()

orders = []

for _ in range(200):
    customer = random.choice(customers)
    product = random.choice(products)
    amount = round(random.uniform(5, 200), 2)
    days_ago = random.randint(0, 29)
    created_at = now - timedelta(days=days_ago)

    orders.append(
        (customer, product, amount, created_at.strftime("%Y-%m-%d"))
    )

cursor.executemany("""
INSERT INTO orders (customer, product, amount, created_at)
VALUES (?, ?, ?, ?)
""", orders)

conn.commit()

cursor.execute("SELECT COUNT(*) FROM orders")
count = cursor.fetchone()[0]

print(f"Seeded {count} orders.")

conn.close()
