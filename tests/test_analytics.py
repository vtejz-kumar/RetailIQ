import sys
sys.path.insert(0, '.')

from src.analytics import (
    calculate_average_daily_sales,
    calculate_days_of_stock,
    classify_risk_level,
    detect_stockout_risk,
    detect_overstock,
    detect_sales_anomalies,
    get_total_revenue,
    get_total_units_sold,
    get_inventory_value,
    get_current_inventory,
    compare_stores,
    get_top_products,
    get_product_performance,
    get_store_performance,
    get_sales_trend,
    get_attention_items,
    RiskLevel
)
from src.database import reset_database
from data.load_data import load_all_data


def setup_module():
    """Set up test database with synthetic data."""
    reset_database()
    load_all_data()


def test_calculate_average_daily_sales():
    """Test average daily sales calculation."""
    # Product 1 (Wireless Headphones) at Hyderabad (store 1) has high sales
    avg = calculate_average_daily_sales(1, 1, days=30)
    assert avg > 0, "Should have positive average for high-selling product"
    
    # Product with no sales should return 0
    avg = calculate_average_daily_sales(999, 999, days=30)
    assert avg == 0.0, "Non-existent product should have 0 average"


def test_calculate_days_of_stock():
    """Test days of stock calculation."""
    # Normal case
    days = calculate_days_of_stock(100, 10)
    assert days == 10.0
    
    # Zero stock
    days = calculate_days_of_stock(0, 10)
    assert days == 0.0
    
    # Zero average daily sales
    days = calculate_days_of_stock(100, 0)
    assert days is None
    
    # Negative average daily sales
    days = calculate_days_of_stock(100, -5)
    assert days is None


def test_classify_risk_level():
    """Test risk level classification."""
    assert classify_risk_level(None) == RiskLevel.NO_SALES
    assert classify_risk_level(0) == RiskLevel.CRITICAL
    assert classify_risk_level(1.5) == RiskLevel.CRITICAL
    assert classify_risk_level(3) == RiskLevel.CRITICAL
    assert classify_risk_level(4) == RiskLevel.HIGH
    assert classify_risk_level(7) == RiskLevel.HIGH
    assert classify_risk_level(8) == RiskLevel.MEDIUM
    assert classify_risk_level(14) == RiskLevel.MEDIUM
    assert classify_risk_level(15) == RiskLevel.HEALTHY
    assert classify_risk_level(100) == RiskLevel.HEALTHY


def test_detect_stockout_risk():
    """Test stockout risk detection."""
    # Get all risks
    risks = detect_stockout_risk()
    assert len(risks) > 0, "Should detect some stockout risks"
    
    # Check CRITICAL risks exist
    critical = detect_stockout_risk(risk_level=RiskLevel.CRITICAL)
    assert len(critical) > 0, "Should have CRITICAL risk items"
    
    # Check sorting: CRITICAL first, then by days remaining
    risks = detect_stockout_risk()
    risk_order = {RiskLevel.CRITICAL: 0, RiskLevel.HIGH: 1, RiskLevel.MEDIUM: 2,
                  RiskLevel.NO_SALES: 3, RiskLevel.HEALTHY: 4}
    
    for i in range(len(risks) - 1):
        curr_order = risk_order[risks[i].risk_level]
        next_order = risk_order[risks[i+1].risk_level]
        assert curr_order <= next_order, "Risks should be sorted by severity"


def test_detect_overstock():
    """Test overstock detection."""
    overstock = detect_overstock()
    assert len(overstock) > 0, "Should detect overstocked items"
    
    # Check sorting: highest days_inventory first
    for i in range(len(overstock) - 1):
        assert overstock[i].days_inventory >= overstock[i+1].days_inventory
    
    # Verify specific known overstock: Bluetooth Speaker at Chennai (store 5)
    chennai_overstock = [o for o in overstock if o.store_id == 5 and o.product_name == "Bluetooth Speaker"]
    assert len(chennai_overstock) > 0, "Bluetooth Speaker at Chennai should be overstocked"
    assert chennai_overstock[0].current_stock == 120


def test_detect_sales_anomalies():
    """Test sales anomaly detection."""
    anomalies = detect_sales_anomalies()
    assert len(anomalies) > 0, "Should detect some anomalies"
    
    # Check for SPIKE and DROP
    spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
    drops = [a for a in anomalies if a.anomaly_type == "DROP"]
    assert len(spikes) > 0, "Should detect spikes"
    assert len(drops) > 0, "Should detect drops"
    
    # Check sorting: highest absolute percentage change first
    for i in range(len(anomalies) - 1):
        assert abs(anomalies[i].pct_change) >= abs(anomalies[i+1].pct_change)
    
    # Verify specific scenarios:
    # Smart Watch at Bengaluru (store 4) - SPIKE
    smart_watch_spike = [a for a in anomalies 
                         if a.store_id == 4 and a.product_name == "Smart Watch" and a.anomaly_type == "SPIKE"]
    assert len(smart_watch_spike) > 0, "Smart Watch at Bengaluru should have spike"
    
    # Power Bank at Vijayawada (store 2) - DROP
    power_bank_drop = [a for a in anomalies 
                       if a.store_id == 2 and a.product_name == "Power Bank 20000mAh" and a.anomaly_type == "DROP"]
    assert len(power_bank_drop) > 0, "Power Bank at Vijayawada should have drop"


def test_get_total_revenue():
    """Test revenue aggregation."""
    total = get_total_revenue()
    assert total > 0, "Total revenue should be positive"
    assert total == 557805080.0  # Expected from generated data


def test_get_total_units_sold():
    """Test units sold aggregation."""
    total = get_total_units_sold()
    assert total > 0
    assert total == 123920


def test_get_inventory_value():
    """Test inventory value calculation."""
    value = get_inventory_value()
    assert value > 0
    assert value == 691010.0


def test_get_current_inventory():
    """Test inventory retrieval."""
    inventory = get_current_inventory()
    assert len(inventory) == 336  # 6 stores * 56 products
    
    # Test filtering
    hyderabad_inv = get_current_inventory(store_id=1)
    assert len(hyderabad_inv) == 56
    
    product_inv = get_current_inventory(product_id=1)
    assert len(product_inv) == 6


def test_compare_stores():
    """Test store comparison."""
    stores = compare_stores()
    assert len(stores) == 6
    
    # Should be sorted by revenue descending
    for i in range(len(stores) - 1):
        assert stores[i]["revenue"] >= stores[i+1]["revenue"]
    
    # Bengaluru should be top (highest multiplier 1.3)
    assert stores[0]["city"] == "Bengaluru"
    # Chennai should be lowest (multiplier 0.85)
    assert stores[-1]["city"] == "Chennai"


def test_get_top_products():
    """Test top products by revenue."""
    top = get_top_products(10)
    assert len(top) == 10
    
    # Should be sorted by revenue descending
    for i in range(len(top) - 1):
        assert top[i]["total_revenue"] >= top[i+1]["total_revenue"]
    
    # Standing Desk should be #1 (high price, high sales)
    assert top[0]["name"] == "Standing Desk"


def test_get_product_performance():
    """Test single product performance."""
    perf = get_product_performance(1)  # Wireless Headphones
    assert perf["id"] == 1
    assert perf["name"] == "Wireless Headphones"
    assert perf["units_sold"] > 0
    assert perf["revenue"] > 0
    
    # Non-existent product
    perf = get_product_performance(999)
    assert perf == {}


def test_get_store_performance():
    """Test single store performance."""
    perf = get_store_performance(1)
    assert perf["units_sold"] > 0
    assert perf["revenue"] > 0
    assert perf["products_sold"] == 56
    assert perf["id"] == 1
    assert perf["city"] == "Hyderabad"
    
    # Non-existent store - returns empty dict
    perf = get_store_performance(999)
    assert perf == {}


def test_get_sales_trend():
    """Test sales trend data."""
    trend = get_sales_trend(30)
    assert len(trend) == 30
    
    for day in trend:
        assert "date" in day
        assert "units" in day
        assert "revenue" in day
        assert day["units"] >= 0
        assert day["revenue"] >= 0


def test_get_attention_items():
    """Test attention items aggregation."""
    attention = get_attention_items()
    
    assert "critical" in attention
    assert "high" in attention
    assert "overstock" in attention
    assert "anomalies" in attention
    
    assert len(attention["critical"]) > 0
    assert len(attention["overstock"]) > 0
    assert len(attention["anomalies"]) > 0


def test_zero_sales_handling():
    """Test products with zero recent sales."""
    risks = detect_stockout_risk()
    no_sales = [r for r in risks if r.risk_level == RiskLevel.NO_SALES]
    assert len(no_sales) > 0, "Should have products with NO_RECENT_SALES"
    
    # These should have days_remaining = None
    for item in no_sales:
        assert item.days_remaining is None


if __name__ == "__main__":
    setup_module()
    
    print("Running analytics tests...")
    test_calculate_average_daily_sales()
    print("✓ Average daily sales test passed")
    
    test_calculate_days_of_stock()
    print("✓ Days of stock test passed")
    
    test_classify_risk_level()
    print("✓ Risk level classification test passed")
    
    test_detect_stockout_risk()
    print("✓ Stockout risk detection test passed")
    
    test_detect_overstock()
    print("✓ Overstock detection test passed")
    
    test_detect_sales_anomalies()
    print("✓ Sales anomalies test passed")
    
    test_get_total_revenue()
    print("✓ Total revenue test passed")
    
    test_get_total_units_sold()
    print("✓ Total units sold test passed")
    
    test_get_inventory_value()
    print("✓ Inventory value test passed")
    
    test_get_current_inventory()
    print("✓ Current inventory test passed")
    
    test_compare_stores()
    print("✓ Store comparison test passed")
    
    test_get_top_products()
    print("✓ Top products test passed")
    
    test_get_product_performance()
    print("✓ Product performance test passed")
    
    test_get_store_performance()
    print("✓ Store performance test passed")
    
    test_get_sales_trend()
    print("✓ Sales trend test passed")
    
    test_get_attention_items()
    print("✓ Attention items test passed")
    
    test_zero_sales_handling()
    print("✓ Zero sales handling test passed")
    
    print("\nAll analytics tests passed!")