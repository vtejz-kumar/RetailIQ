import csv
import sqlite3
from pathlib import Path
from src.config import settings
from src.database import init_database, get_connection


def load_csv_to_table(table_name: str, csv_path: Path, columns: list):
    conn = get_connection()
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [tuple(row[col] for col in columns) for row in reader]

        placeholders = ", ".join(["?"] * len(columns))
        columns_str = ", ".join(columns)

        conn.executemany(
            f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})",
            rows
        )
        conn.commit()
        print(f"Loaded {len(rows)} rows into {table_name}")
    finally:
        conn.close()


def load_all_data():
    data_dir = Path("data")

    # Initialize database
    init_database()

    # Load stores
    load_csv_to_table(
        "stores",
        data_dir / "stores.csv",
        ["id", "name", "city", "region"]
    )

    # Load products
    load_csv_to_table(
        "products",
        data_dir / "products.csv",
        ["id", "name", "category", "price", "cost", "reorder_threshold", "target_stock"]
    )

    # Load sales
    load_csv_to_table(
        "sales",
        data_dir / "sales.csv",
        ["id", "date", "store_id", "product_id", "quantity", "revenue"]
    )

    # Load inventory
    load_csv_to_table(
        "inventory",
        data_dir / "inventory.csv",
        ["id", "snapshot_date", "store_id", "product_id", "stock_quantity"]
    )

    print("\nAll data loaded successfully!")


if __name__ == "__main__":
    load_all_data()