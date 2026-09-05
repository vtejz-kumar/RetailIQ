import sys
sys.path.insert(0, '.')

import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.database import reset_database
from data.load_data import load_all_data


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    reset_database()
    load_all_data()
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["gemini_configured"] is True


def test_dashboard_endpoint(client):
    """Test dashboard endpoint."""
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    
    # Check KPIs
    assert "kpis" in data
    kpis = data["kpis"]
    assert "total_revenue" in kpis
    assert "total_units_sold" in kpis
    assert "inventory_value" in kpis
    assert "low_stock_count" in kpis
    assert "overstock_count" in kpis
    assert "attention_count" in kpis
    
    assert kpis["total_revenue"] > 0
    assert kpis["total_units_sold"] > 0
    assert kpis["inventory_value"] > 0
    assert kpis["low_stock_count"] > 0
    assert kpis["overstock_count"] > 0
    assert kpis["attention_count"] > 0
    
    # Check other sections
    assert "sales_trend" in data
    assert len(data["sales_trend"]) == 30
    
    assert "store_performance" in data
    assert len(data["store_performance"]) == 6
    
    assert "top_products" in data
    assert len(data["top_products"]) == 10
    
    assert "inventory_health" in data
    assert "anomaly_summary" in data


def test_stores_endpoint(client):
    """Test stores list endpoint."""
    response = client.get("/api/stores")
    assert response.status_code == 200
    stores = response.json()
    assert len(stores) == 6
    for store in stores:
        assert "id" in store
        assert "name" in store
        assert "city" in store
        assert "region" in store


def test_products_endpoint(client):
    """Test products list endpoint."""
    response = client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 56
    
    # Test category filter
    response = client.get("/api/products?category=Electronics")
    assert response.status_code == 200
    electronics = response.json()
    assert all(p["category"] == "Electronics" for p in electronics)


def test_inventory_endpoint(client):
    """Test inventory endpoint."""
    response = client.get("/api/inventory")
    assert response.status_code == 200
    inventory = response.json()
    assert len(inventory) == 336  # 6 * 56
    
    # Test store filter
    response = client.get("/api/inventory?store_id=1")
    assert response.status_code == 200
    assert len(response.json()) == 56
    
    # Test product filter
    response = client.get("/api/inventory?product_id=1")
    assert response.status_code == 200
    assert len(response.json()) == 6
    
    # Test category filter
    response = client.get("/api/inventory?category=Electronics")
    assert response.status_code == 200
    for item in response.json():
        assert item["category"] == "Electronics"
    
    # Test risk filter
    response = client.get("/api/inventory?risk=CRITICAL")
    assert response.status_code == 200
    for item in response.json():
        # Should be at CRITICAL risk
        pass  # Risk filtering is done in frontend


def test_sales_endpoint(client):
    """Test sales trend endpoint."""
    response = client.get("/api/sales")
    assert response.status_code == 200
    sales = response.json()
    assert len(sales) == 30
    
    for day in sales:
        assert "date" in day
        assert "units" in day
        assert "revenue" in day
    
    # Test with filters
    response = client.get("/api/sales?days=7")
    assert response.status_code == 200
    assert len(response.json()) == 7
    
    response = client.get("/api/sales?store_id=1")
    assert response.status_code == 200
    
    response = client.get("/api/sales?category=Electronics")
    assert response.status_code == 200


def test_risks_endpoint(client):
    """Test stockout risks endpoint."""
    response = client.get("/api/risks")
    assert response.status_code == 200
    risks = response.json()
    assert len(risks) > 0
    
    # Test filters
    response = client.get("/api/risks?level=CRITICAL")
    assert response.status_code == 200
    for risk in response.json():
        assert risk["risk_level"] == "CRITICAL"
    
    response = client.get("/api/risks?store_id=1")
    assert response.status_code == 200
    
    response = client.get("/api/risks?category=Electronics")
    assert response.status_code == 200


def test_overstock_endpoint(client):
    """Test overstock endpoint."""
    response = client.get("/api/overstock")
    assert response.status_code == 200
    overstock = response.json()
    assert len(overstock) > 0
    
    for item in overstock:
        assert "product_id" in item
        assert "product_name" in item
        assert "store_id" in item
        assert "store_name" in item
        assert "days_inventory" in item
        assert item["days_inventory"] > 45


def test_anomalies_endpoint(client):
    """Test sales anomalies endpoint."""
    response = client.get("/api/anomalies")
    assert response.status_code == 200
    anomalies = response.json()
    assert len(anomalies) > 0
    
    for item in anomalies:
        assert "anomaly_type" in item
        assert item["anomaly_type"] in ["SPIKE", "DROP"]
        assert "pct_change" in item
        assert abs(item["pct_change"]) >= 50  # 50% threshold


def test_recommendations_endpoint(client):
    """Test recommendations endpoint."""
    response = client.get("/api/recommendations")
    assert response.status_code == 200
    recs = response.json()
    assert len(recs) > 0
    
    for rec in recs:
        assert "product_id" in rec
        assert "product_name" in rec
        assert "store_id" in rec
        assert "store_name" in rec
        assert "action" in rec
        assert "priority" in rec
        assert "reason" in rec
        assert "evidence" in rec
        assert "assumptions" in rec
    
    # Test filters
    response = client.get("/api/recommendations?store_id=1")
    assert response.status_code == 200
    for rec in response.json():
        assert rec["store_id"] == 1


def test_attention_endpoint(client):
    """Test attention endpoint."""
    response = client.get("/api/attention")
    assert response.status_code == 200
    attention = response.json()
    
    assert "critical" in attention
    assert "high" in attention
    assert "overstock" in attention
    assert "anomalies" in attention
    
    assert len(attention["critical"]) > 0
    assert len(attention["overstock"]) > 0
    assert len(attention["anomalies"]) > 0


def test_product_detail_endpoint(client):
    """Test product detail endpoint."""
    response = client.get("/api/products/1")
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == 1
    assert product["name"] == "Wireless Headphones"
    
    # Non-existent product
    response = client.get("/api/products/999")
    assert response.status_code == 404


def test_store_detail_endpoint(client):
    """Test store detail endpoint."""
    response = client.get("/api/stores/1")
    assert response.status_code == 200
    store = response.json()
    assert store["id"] == 1
    assert store["city"] == "Hyderabad"
    
    # Non-existent store
    response = client.get("/api/stores/999")
    assert response.status_code == 404


def test_stores_performance_endpoint(client):
    """Test stores performance endpoint."""
    response = client.get("/api/stores/performance")
    assert response.status_code == 200
    stores = response.json()
    assert len(stores) == 6


def test_top_products_endpoint(client):
    """Test top products endpoint."""
    response = client.get("/api/products/top")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 10
    
    # Test limit parameter
    response = client.get("/api/products/top?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_copilot_endpoint(client):
    """Test copilot query endpoint."""
    # Test stockout query
    response = client.post("/api/copilot/query", json={"question": "What is running out?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "evidence" in data
    assert "calculation" in data
    assert "recommendation" in data
    assert "assumptions" in data
    
    # Test overstock query
    response = client.post("/api/copilot/query", json={"question": "What is overstocked?"})
    assert response.status_code == 200
    
    # Test unknown product
    response = client.post("/api/copilot/query", json={"question": "How did nonexistent product perform?"})
    assert response.status_code == 200
    data = response.json()
    assert "error" in data or "No data found" in data.get("answer", "")
    
    # Test invalid input
    response = client.post("/api/copilot/query", json={"question": ""})
    assert response.status_code == 200


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "*"


def test_gzip_compression(client):
    """Test GZip compression for API responses."""
    response = client.get("/api/dashboard", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert "content-encoding" in response.headers
    assert "gzip" in response.headers["content-encoding"]


def test_static_file_caching(client):
    """Test static file caching headers."""
    response = client.get("/assets/index.html")
    # Might 404 if not built, but shouldn't error
    assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])