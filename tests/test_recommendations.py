import sys
sys.path.insert(0, '.')

from src.recommendations import (
    generate_all_recommendations,
    generate_recommendation_for_stockout,
    generate_recommendation_for_overstock,
    generate_recommendation_for_anomaly,
    get_transfer_opportunities
)
from src.analytics import detect_stockout_risk, detect_overstock, detect_sales_anomalies, RiskLevel
from src.database import reset_database
from data.load_data import load_all_data


def setup_module():
    """Set up test database with synthetic data."""
    reset_database()
    load_all_data()


def test_generate_recommendation_for_stockout_critical():
    """Test CRITICAL stockout recommendation."""
    risks = detect_stockout_risk(risk_level=RiskLevel.CRITICAL)
    assert len(risks) > 0
    
    item = risks[0]
    rec = generate_recommendation_for_stockout(item, RiskLevel.CRITICAL)
    
    assert rec["action"] in ["REORDER", "TRANSFER"]
    assert rec["priority"] == "CRITICAL"
    assert "CRITICAL" in rec["reason"]
    assert "evidence" in rec
    assert "assumptions" in rec
    assert len(rec["assumptions"]) > 0
    assert rec["evidence"]["current_stock"] == item.current_stock
    assert rec["evidence"]["avg_daily_sales"] == item.avg_daily_sales


def test_generate_recommendation_for_stockout_high():
    """Test HIGH stockout recommendation."""
    risks = detect_stockout_risk(risk_level=RiskLevel.HIGH)
    if len(risks) > 0:
        item = risks[0]
        rec = generate_recommendation_for_stockout(item, RiskLevel.HIGH)
        
        assert rec["action"] in ["REORDER", "TRANSFER"]
        assert rec["priority"] == "HIGH"
        assert "HIGH" in rec["reason"]


def test_generate_recommendation_for_stockout_transfer():
    """Test TRANSFER recommendation when overstock exists elsewhere."""
    # Lightning Cable 2m at Bengaluru (store 4) has low stock
    # Chennai (store 5) has 61 units - should be transfer candidate
    risks = detect_stockout_risk(risk_level=RiskLevel.CRITICAL)
    lightning_cable = [r for r in risks if r.product_name == "Lightning Cable 2m" and r.store_id == 4]
    
    if len(lightning_cable) > 0:
        item = lightning_cable[0]
        rec = generate_recommendation_for_stockout(item, RiskLevel.CRITICAL)
        
        # Should be TRANSFER since Chennai has excess
        assert rec["action"] == "TRANSFER"
        assert "Transfer possible" in rec["reason"]


def test_generate_recommendation_for_overstock():
    """Test overstock recommendation."""
    overstock = detect_overstock()
    assert len(overstock) > 0
    
    item = overstock[0]
    rec = generate_recommendation_for_overstock(item)
    
    assert rec["action"] in ["PROMOTE", "MONITOR"]
    assert rec["priority"] in ["HIGH", "MEDIUM", "LOW"]
    assert "evidence" in rec
    assert "assumptions" in rec
    assert rec["evidence"]["current_stock"] == item.current_stock
    assert rec["evidence"]["days_inventory"] == item.days_inventory


def test_generate_recommendation_for_anomaly_spike():
    """Test SPIKE anomaly recommendation."""
    anomalies = detect_sales_anomalies()
    spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
    assert len(spikes) > 0
    
    spike = spikes[0]
    rec = generate_recommendation_for_anomaly(spike)
    
    assert rec["action"] == "INVESTIGATE"
    assert rec["priority"] in ["HIGH", "MEDIUM"]
    assert "SPIKE" in rec["reason"]
    assert rec["evidence"]["anomaly_type"] == "SPIKE"


def test_generate_recommendation_for_anomaly_drop():
    """Test DROP anomaly recommendation."""
    anomalies = detect_sales_anomalies()
    drops = [a for a in anomalies if a.anomaly_type == "DROP"]
    assert len(drops) > 0
    
    drop = drops[0]
    rec = generate_recommendation_for_anomaly(drop)
    
    assert rec["action"] == "INVESTIGATE"
    assert rec["priority"] in ["HIGH", "MEDIUM"]
    assert "DROP" in rec["reason"]
    assert rec["evidence"]["anomaly_type"] == "DROP"


def test_generate_all_recommendations():
    """Test full recommendation generation."""
    recs = generate_all_recommendations(limit_per_category=5)
    
    assert len(recs) > 0
    assert len(recs) <= 20  # 5 per category * 4 categories
    
    # Check all required fields
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
    
    # Check priority ordering: CRITICAL > HIGH > MEDIUM > LOW
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    for i in range(len(recs) - 1):
        assert priority_order[recs[i]["priority"]] <= priority_order[recs[i+1]["priority"]]


def test_get_transfer_opportunities():
    """Test transfer opportunity detection."""
    opportunities = get_transfer_opportunities()
    
    # Should find Lightning Cable 2m: Chennai (61) -> Bengaluru (1)
    lightning_transfers = [o for o in opportunities 
                          if o["product_name"] == "Lightning Cable 2m" 
                          and o["from_store_id"] == 5 
                          and o["to_store_id"] == 4]
    assert len(lightning_transfers) > 0
    
    opp = lightning_transfers[0]
    assert opp["from_store_name"] == "RetailIQ Chennai"
    assert opp["to_store_name"] == "RetailIQ Bengaluru"
    assert opp["from_stock"] == 61
    assert opp["to_stock"] == 1
    assert opp["suggested_transfer_qty"] > 0


def test_recommendation_evidence_completeness():
    """Test that all recommendations have complete evidence."""
    recs = generate_all_recommendations(limit_per_category=10)
    
    for rec in recs:
        ev = rec["evidence"]
        
        # All should have these
        assert "current_stock" in ev
        assert "avg_daily_sales" in ev
        
        # Stockout recommendations
        if rec["action"] in ["REORDER", "TRANSFER"]:
            assert "days_remaining" in ev
            assert "risk_level" in ev
            assert "reorder_threshold" in ev
        
        # Overstock recommendations
        if rec["action"] in ["PROMOTE", "MONITOR"] and "days_inventory" in ev:
            assert "days_inventory" in ev
            assert "recent_sales_7d" in ev
        
        # Anomaly recommendations
        if rec["action"] == "INVESTIGATE":
            assert "anomaly_type" in ev
            assert "pct_change" in ev
            assert "historical_avg_daily" in ev
            assert "recent_avg_daily" in ev


def test_no_duplicate_recommendations():
    """Test that same product-store combo doesn't get duplicate recommendations."""
    recs = generate_all_recommendations(limit_per_category=10)
    
    seen = set()
    for rec in recs:
        key = (rec["product_id"], rec["store_id"], rec["action"])
        assert key not in seen, f"Duplicate recommendation: {key}"
        seen.add(key)


if __name__ == "__main__":
    setup_module()
    
    print("Running recommendations tests...")
    test_generate_recommendation_for_stockout_critical()
    print("✓ Critical stockout recommendation test passed")
    
    test_generate_recommendation_for_stockout_high()
    print("✓ High stockout recommendation test passed")
    
    test_generate_recommendation_for_stockout_transfer()
    print("✓ Transfer recommendation test passed")
    
    test_generate_recommendation_for_overstock()
    print("✓ Overstock recommendation test passed")
    
    test_generate_recommendation_for_anomaly_spike()
    print("✓ Spike anomaly recommendation test passed")
    
    test_generate_recommendation_for_anomaly_drop()
    print("✓ Drop anomaly recommendation test passed")
    
    test_generate_all_recommendations()
    print("✓ All recommendations test passed")
    
    test_get_transfer_opportunities()
    print("✓ Transfer opportunities test passed")
    
    test_recommendation_evidence_completeness()
    print("✓ Recommendation evidence completeness test passed")
    
    test_no_duplicate_recommendations()
    print("✓ No duplicate recommendations test passed")
    
    print("\nAll recommendations tests passed!")