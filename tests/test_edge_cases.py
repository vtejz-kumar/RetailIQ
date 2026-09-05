import sys
sys.path.insert(0, '.')

from src.analytics import (
    detect_stockout_risk,
    detect_overstock,
    detect_sales_anomalies,
    calculate_average_daily_sales,
    calculate_days_of_stock,
    classify_risk_level,
    get_total_revenue,
    get_total_units_sold,
    get_inventory_value,
    get_current_inventory,
    compare_stores,
    get_top_products,
    get_product_performance,
    get_store_performance,
    get_sales_trend,
    RiskLevel
)
from src.recommendations import generate_all_recommendations
from src.database import reset_database
from data.load_data import load_all_data


def setup_module():
    """Set up test database with synthetic data."""
    reset_database()
    load_all_data()


def test_zero_sales_product():
    """Test product with zero sales handled correctly."""
    # Product 7 (Portable SSD) at Visakhapatnam (store 3) has zero recent sales
    avg = calculate_average_daily_sales(7, 3, days=7)
    assert avg == 0.0, "Recent 7-day average should be 0"
    
    days = calculate_days_of_stock(45, 0)
    assert days is None, "Days remaining should be None for zero sales"
    
    risk = classify_risk_level(None)
    assert risk == RiskLevel.NO_SALES


def test_zero_inventory():
    """Test product with zero inventory."""
    # Smart Watch at Hyderabad (store 1) has 0 stock
    risks = detect_stockout_risk()
    smart_watch_hyd = [r for r in risks if r.product_name == "Smart Watch" and r.store_id == 1]
    assert len(smart_watch_hyd) > 0
    
    item = smart_watch_hyd[0]
    assert item.current_stock == 0
    assert item.risk_level == RiskLevel.CRITICAL
    assert item.days_remaining is None


def test_unknown_product_lookup():
    """Test analytics with non-existent product ID."""
    avg = calculate_average_daily_sales(99999, 1, days=30)
    assert avg == 0.0, "Non-existent product should have 0 average"
    
    perf = get_product_performance(99999)
    assert perf == {}, "Non-existent product should return empty dict"


def test_unknown_store_lookup():
    """Test analytics with non-existent store ID."""
    avg = calculate_average_daily_sales(1, 99999, days=30)
    assert avg == 0.0, "Non-existent store should have 0 average"
    
    perf = get_store_performance(99999)
    assert perf == {}


def test_no_matching_records():
    """Test queries that return no matching records."""
    # Filter for non-existent category
    risks = detect_stockout_risk(category="NonExistentCategory")
    assert len(risks) == 0
    
    overstock = detect_overstock(category="NonExistentCategory")
    assert len(overstock) == 0
    
    anomalies = detect_sales_anomalies(category="NonExistentCategory")
    assert len(anomalies) == 0


def test_insufficient_history():
    """Test products with insufficient sales history."""
    # All products have 90 days history, but test with very short window
    avg = calculate_average_daily_sales(1, 1, days=1)
    # Should still work with 1 day window
    assert avg >= 0


def test_empty_date_range():
    """Test sales trend with date range that has no data."""
    # Future dates
    trend = get_sales_trend(days=30)
    # Should still return data from available range
    assert len(trend) <= 30


def test_division_by_zero_protection():
    """Test all division by zero cases are handled."""
    # Days of stock with zero sales
    assert calculate_days_of_stock(100, 0) is None
    assert calculate_days_of_stock(0, 0) is None
    assert calculate_days_of_stock(-10, 0) is None
    
    # Risk classification with None
    assert classify_risk_level(None) == RiskLevel.NO_SALES


def test_negative_values():
    """Test handling of negative values (should not occur but defensive)."""
    # Negative stock
    days = calculate_days_of_stock(-10, 5)
    assert days == -2.0  # Math works, but business logic should prevent
    
    # Negative average sales
    days = calculate_days_of_stock(100, -5)
    assert days is None  # Protected


def test_large_numbers():
    """Test handling of large numbers."""
    # Very high stock, very low sales
    days = calculate_days_of_stock(1000000, 0.001)
    assert days == 1000000000.0
    
    # Very high sales
    days = calculate_days_of_stock(100, 1000)
    assert days == 0.1


def test_recommendation_edge_cases():
    """Test recommendations with edge cases."""
    recs = generate_all_recommendations(limit_per_category=20)
    
    # Should handle all categories
    actions = {rec["action"] for rec in recs}
    assert "REORDER" in actions or "TRANSFER" in actions  # Stockout
    assert "PROMOTE" in actions or "MONITOR" in actions  # Overstock
    assert "INVESTIGATE" in actions  # Anomalies
    
    # All should have required fields
    for rec in recs:
        assert rec["product_id"] > 0
        assert rec["store_id"] > 0
        assert len(rec["product_name"]) > 0
        assert len(rec["store_name"]) > 0
        assert rec["priority"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert isinstance(rec["assumptions"], list)
        assert len(rec["assumptions"]) > 0


def test_api_error_handling():
    """Test API error responses."""
    from fastapi.testclient import TestClient
    from src.api import app
    from src.database import reset_database
    from data.load_data import load_all_data
    
    reset_database()
    load_all_data()
    client = TestClient(app)
    
    # Test 404 for non-existent product
    response = client.get("/api/products/99999")
    assert response.status_code == 404
    
    # Test 404 for non-existent store
    response = client.get("/api/stores/99999")
    assert response.status_code == 404
    
    # Test validation error for invalid copilot query
    response = client.post("/api/copilot/query", json={"question": 123})
    assert response.status_code == 422  # Validation error


def test_copilot_missing_question():
    """Test copilot with missing question field."""
    from fastapi.testclient import TestClient
    from src.api import app
    
    client = TestClient(app)
    response = client.post("/api/copilot/query", json={})
    assert response.status_code == 422  # Validation error


def test_concurrent_requests():
    """Test handling of concurrent requests."""
    import threading
    import time
    from fastapi.testclient import TestClient
    from src.api import app
    from src.database import reset_database
    from data.load_data import load_all_data
    
    reset_database()
    load_all_data()
    client = TestClient(app)
    
    results = []
    errors = []
    
    def make_request():
        try:
            response = client.get("/api/dashboard")
            results.append(response.status_code)
        except Exception as e:
            errors.append(str(e))
    
    threads = [threading.Thread(target=make_request) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert all(code == 200 for code in results)


def test_database_locking():
    """Test database handles concurrent access."""
    import threading
    from src.analytics import get_total_revenue
    
    results = []
    
    def query_revenue():
        try:
            rev = get_total_revenue()
            results.append(rev)
        except Exception as e:
            results.append(f"Error: {e}")
    
    threads = [threading.Thread(target=query_revenue) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(results) == 20
    assert all(isinstance(r, (int, float)) for r in results)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-x"])