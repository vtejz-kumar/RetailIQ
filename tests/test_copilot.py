import sys
sys.path.insert(0, '.')

import pytest
from src.copilot import process_copilot_query, execute_intent
from src.gemini_client import gemini_client
from src.models import CopilotIntent
from src.database import reset_database
from data.load_data import load_all_data


def setup_module():
    """Set up test database with synthetic data."""
    reset_database()
    load_all_data()


def is_gemini_available():
    """Check if Gemini API is available (not rate limited)."""
    if not gemini_client.is_configured():
        return False
    try:
        intent = gemini_client.extract_intent("test")
        return intent is not None
    except Exception:
        return False


def test_copilot_without_gemini_key(monkeypatch):
    """Test copilot behavior when Gemini key not configured."""
    from src.config import settings
    from src.gemini_client import GeminiClient
    import src.copilot as copilot_module
    
    original_key = settings.gemini_api_key
    monkeypatch.setattr(settings, 'gemini_api_key', '')
    
    new_client = GeminiClient()
    original_client = copilot_module.gemini_client
    copilot_module.gemini_client = new_client
    
    try:
        result = process_copilot_query("What is running out?")
        assert "error" in result
        assert result["error"] == "GEMINI_API_KEY not configured"
        assert "AI Copilot is not configured" in result["answer"]
    finally:
        copilot_module.gemini_client = original_client
        monkeypatch.setattr(settings, 'gemini_api_key', original_key)


def test_copilot_invalid_intent():
    """Test copilot with invalid/malformed intent."""
    import src.copilot as copilot_module
    
    class MockGeminiClient:
        def is_configured(self):
            return True
        
        def extract_intent(self, question):
            return CopilotIntent(intent="invalid_intent_xyz")
        
        def explain_results(self, question, intent, data):
            return {
                "answer": "I couldn't understand your question.",
                "evidence": "",
                "calculation": "",
                "recommendation": "Try rephrasing your question.",
                "assumptions": "",
                "error": "Intent extraction failed"
            }
    
    import src.copilot as copilot_module
    original_client = copilot_module.gemini_client
    copilot_module.gemini_client = MockGeminiClient()
    
    try:
        result = process_copilot_query("test")
        assert "error" in result
        assert result["error"] == "Intent extraction failed"
    finally:
        copilot_module.gemini_client = gemini_client


def test_copilot_intent_extraction():
    """Test intent extraction for various queries."""
    if not gemini_client.is_configured():
        pytest.skip("Gemini API not available (rate limited or not configured)")
    
    try:
        intent = gemini_client.extract_intent("test")
        if intent is None:
            pytest.skip("Gemini API rate limited")
    except Exception:
        pytest.skip("Gemini API not available (rate limited)")
    
    test_cases = [
        ("What is running out?", "stock_out"),
        ("What's overstocked?", "overstock"),
        ("How did laptops perform this month?", "product_performance"),
        ("Which store performed best?", "store_performance"),
        ("What should I reorder today?", "recommendation"),
        ("Which products had sales drops?", "sales_anomaly"),
        ("Compare Hyderabad and Vijayawada", "comparison"),
        ("What's in stock?", "inventory_status"),
        ("Show me the dashboard", "general_data_question"),
    ]
    
    for question, expected_intent in test_cases:
        intent = gemini_client.extract_intent(question)
        assert intent is not None, f"Failed to extract intent for: {question}"
        assert intent.intent == expected_intent, f"Wrong intent for '{question}': got {intent.intent}, expected {expected_intent}"


def test_copilot_stockout_query():
    """Test copilot stockout query returns correct data."""
    if not gemini_client.is_configured():
        pytest.skip("Gemini API not available (rate limited or not configured)")
    
    try:
        intent = gemini_client.extract_intent("test")
        if intent is None:
            pytest.skip("Gemini API rate limited")
    except Exception:
        pytest.skip("Gemini API rate limited")
    
    result = process_copilot_query("What is running out?")
    
    assert "answer" in result
    assert "evidence" in result
    assert "calculation" in result
    assert "recommendation" in result
    assert "assumptions" in result
    
    if "error" in result and "quota" not in result.get("error", "").lower():
        pytest.fail(f"Unexpected error: {result['error']}")


def test_copilot_overstock_query():
    """Test copilot overstock query."""
    if not gemini_client.is_configured():
        pytest.skip("Gemini not configured")
    
    result = process_copilot_query("What is overstocked?")
    assert "answer" in result
    assert "evidence" in result


def test_copilot_recommendation_query():
    """Test copilot recommendation query."""
    if not gemini_client.is_configured():
        pytest.skip("Gemini not configured")
    
    result = process_copilot_query("What should I reorder today?")
    assert "answer" in result
    assert "evidence" in result


def test_copilot_comparison_query():
    """Test copilot store comparison query."""
    if not gemini_client.is_configured():
        pytest.skip("Gemini not configured")
    
    result = process_copilot_query("Compare Hyderabad and Vijayawada")
    assert "answer" in result
    assert "evidence" in result


def test_copilot_unknown_product():
    """Test copilot with unknown product."""
    if not gemini_client.is_configured():
        pytest.skip("Gemini not configured")
    
    result = process_copilot_query("How did nonexistent product XYZ perform?")
    assert "answer" in result


def test_copilot_unsupported_question():
    """Test copilot with unsupported question (forecasting)."""
    if not gemini_client.is_configured():
        pytest.skip("Gemini API not available (rate limited or not configured)")
    
    try:
        intent = gemini_client.extract_intent("test")
        if intent is None:
            pytest.skip("Gemini API rate limited")
    except Exception:
        pytest.skip("Gemini API rate limited")
    
    result = process_copilot_query("What will sales be next year?")
    
    answer = result.get("answer", "").lower()
    assert any(word in answer for word in ["cannot", "can't", "unable", "forecast", "predict", "don't have", "not enough", "reliably"]), \
        f"Should refuse forecasting, got: {result.get('answer')}"


def test_copilot_empty_results():
    """Test copilot with query that returns no data."""
    intent = CopilotIntent(
        intent="product_performance",
        product="NonexistentProduct12345",
        store=None,
        category=None,
        time_range=None,
        date_from=None,
        date_to=None
    )
    
    result = execute_intent(intent)
    assert "data" in result
    assert result["data"] == [] or result["data"] == {}


def test_execute_intent_stockout():
    """Test execute_intent for stockout."""
    intent = CopilotIntent(
        intent="stock_out",
        product=None,
        store=None,
        category=None,
        time_range=None,
        date_from=None,
        date_to=None
    )
    
    result = execute_intent(intent)
    assert result["intent"] == "stock_out"
    assert "data" in result
    assert "summary" in result
    assert len(result["data"]) > 0


def test_execute_intent_overstock():
    """Test execute_intent for overstock."""
    intent = CopilotIntent(
        intent="overstock",
        product=None,
        store=None,
        category=None,
        time_range=None,
        date_from=None,
        date_to=None
    )
    
    result = execute_intent(intent)
    assert result["intent"] == "overstock"
    assert "data" in result
    assert len(result["data"]) > 0


def test_execute_intent_anomaly():
    """Test execute_intent for sales anomaly."""
    intent = CopilotIntent(
        intent="sales_anomaly",
        product=None,
        store=None,
        category=None,
        time_range=None,
        date_from=None,
        date_to=None
    )
    
    result = execute_intent(intent)
    assert result["intent"] == "sales_anomaly"
    assert "data" in result
    assert len(result["data"]) > 0


def test_execute_intent_recommendation():
    """Test execute_intent for recommendation."""
    intent = CopilotIntent(
        intent="recommendation",
        product=None,
        store=None,
        category=None,
        time_range=None,
        date_from=None,
        date_to=None
    )
    
    result = execute_intent(intent)
    assert result["intent"] == "recommendation"
    assert "data" in result
    assert len(result["data"]) > 0


def test_execute_intent_comparison():
    """Test execute_intent for store comparison."""
    intent = CopilotIntent(
        intent="comparison",
        product=None,
        store="Hyderabad and Vijayawada",
        category=None,
        time_range=None,
        date_from=None,
        date_to=None
    )
    
    result = execute_intent(intent)
    assert result["intent"] == "comparison"
    assert "data" in result
    assert "store1" in result["data"]
    assert "store2" in result["data"]


def test_intent_filter_by_store():
    """Test intent filtering by store."""
    intent = CopilotIntent(
        intent="stock_out",
        product=None,
        store="Hyderabad",
        category=None,
        time_range=None,
        date_from=None,
        date_to=None
    )
    
    result = execute_intent(intent)
    assert result["intent"] == "stock_out"
    for item in result["data"]:
        assert item["store_name"] == "RetailIQ Hyderabad"


def test_intent_filter_by_category():
    """Test intent filtering by category."""
    intent = CopilotIntent(
        intent="overstock",
        product=None,
        store=None,
        category="Electronics",
        time_range=None,
        date_from=None,
        date_to=None
    )
    
    result = execute_intent(intent)
    assert result["intent"] == "overstock"
    for item in result["data"]:
        assert item["category"] == "Electronics"


def test_intent_filter_by_time_range():
    """Test intent filtering by time range."""
    intent = CopilotIntent(
        intent="sales_trend",
        product=None,
        store=None,
        category=None,
        time_range="7_days",
        date_from=None,
        date_to=None
    )
    
    result = execute_intent(intent)
    assert result["intent"] == "sales_trend"
    assert len(result["data"]) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x"])