import sys
sys.path.insert(0, '.')

import sqlite3
from src.database import init_database, database_exists, get_table_counts, get_connection, reset_database
from src.config import settings
from pathlib import Path


def test_database_creation():
    """Test that database tables are created correctly."""
    reset_database()
    assert database_exists()
    
    conn = get_connection()
    try:
        # Check all tables exist
        tables = ["stores", "products", "sales", "inventory"]
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()["count"]
            assert count >= 0, f"Table {table} should exist"
        
        # Check indexes exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row["name"] for row in cursor.fetchall()]
        expected_indexes = [
            "idx_sales_date",
            "idx_sales_store_product", 
            "idx_inventory_store_product",
            "idx_inventory_snapshot"
        ]
        for idx in expected_indexes:
            assert idx in indexes, f"Index {idx} should exist"
    finally:
        conn.close()


def test_table_counts_after_load():
    """Test expected row counts after data load."""
    from data.load_data import load_all_data
    
    reset_database()
    load_all_data()
    
    counts = get_table_counts()
    
    # Verify expected minimums based on generated data
    assert counts["stores"] == 6, f"Expected 6 stores, got {counts['stores']}"
    assert counts["products"] == 56, f"Expected 56 products, got {counts['products']}"
    assert counts["sales"] > 20000, f"Expected >20000 sales records, got {counts['sales']}"
    assert counts["inventory"] == 336, f"Expected 336 inventory records (6*56), got {counts['inventory']}"


def test_foreign_key_constraints():
    """Test that foreign key relationships work."""
    from data.load_data import load_all_data
    
    reset_database()
    load_all_data()
    
    conn = get_connection()
    try:
        # Test stores -> sales FK
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM sales s
            LEFT JOIN stores st ON s.store_id = st.id
            WHERE st.id IS NULL
        """)
        assert cursor.fetchone()["count"] == 0, "All sales should have valid store_id"
        
        # Test products -> sales FK
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            WHERE p.id IS NULL
        """)
        assert cursor.fetchone()["count"] == 0, "All sales should have valid product_id"
        
        # Test inventory -> stores FK
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM inventory i
            LEFT JOIN stores st ON i.store_id = st.id
            WHERE st.id IS NULL
        """)
        assert cursor.fetchone()["count"] == 0, "All inventory should have valid store_id"
        
        # Test inventory -> products FK
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM inventory i
            LEFT JOIN products p ON i.product_id = p.id
            WHERE p.id IS NULL
        """)
        assert cursor.fetchone()["count"] == 0, "All inventory should have valid product_id"
    finally:
        conn.close()


def test_revenue_calculation():
    """Test that revenue = quantity * price for all sales."""
    from data.load_data import load_all_data
    
    reset_database()
    load_all_data()
    
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT s.id, s.quantity, s.revenue, p.price,
                   (s.quantity * p.price) as calculated_revenue
            FROM sales s
            JOIN products p ON s.product_id = p.id
        """)
        for row in cursor.fetchall():
            expected = round(row["quantity"] * row["price"], 2)
            actual = round(row["revenue"], 2)
            assert expected == actual, f"Revenue mismatch for sale {row['id']}: {expected} != {actual}"
    finally:
        conn.close()


if __name__ == "__main__":
    print("Running database tests...")
    test_database_creation()
    print("✓ Database creation test passed")
    
    test_table_counts_after_load()
    print("✓ Table counts test passed")
    
    test_foreign_key_constraints()
    print("✓ Foreign key constraints test passed")
    
    test_revenue_calculation()
    print("✓ Revenue calculation test passed")
    
    print("\nAll database tests passed!")