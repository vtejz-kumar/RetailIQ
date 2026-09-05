import sqlite3
import os
from pathlib import Path
from src.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    city TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    cost REAL NOT NULL,
    reorder_threshold INTEGER NOT NULL DEFAULT 10,
    target_stock INTEGER NOT NULL DEFAULT 50
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    store_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    revenue REAL NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    store_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    stock_quantity INTEGER NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date);
CREATE INDEX IF NOT EXISTS idx_sales_store_product ON sales(store_id, product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_store_product ON inventory(store_id, product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_snapshot ON inventory(snapshot_date);
"""


def get_connection():
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def database_exists() -> bool:
    return Path(settings.database_path).exists()


def get_table_counts() -> dict:
    conn = get_connection()
    try:
        tables = ["stores", "products", "sales", "inventory"]
        counts = {}
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
            counts[table] = cursor.fetchone()["count"]
        return counts
    finally:
        conn.close()


def reset_database():
    if Path(settings.database_path).exists():
        Path(settings.database_path).unlink()
    init_database()