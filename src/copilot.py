from typing import Dict, Any, Optional, List
from src.gemini_client import gemini_client
from src.analytics import (
    detect_stockout_risk, detect_overstock, detect_sales_anomalies,
    get_product_performance, get_store_performance, compare_stores,
    get_sales_trend, get_all_products, get_all_stores, get_current_inventory,
    get_dashboard_data, get_attention_items, calculate_average_daily_sales,
    get_recent_sales, RiskLevel
)
from src.recommendations import generate_all_recommendations
from src.models import CopilotIntent
from src.config import settings
from src.database import get_connection


def find_product_id(name: str) -> Optional[int]:
    """Find product ID by fuzzy name match."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT id, name FROM products")
        for row in cursor.fetchall():
            if name.lower() in row["name"].lower() or row["name"].lower() in name.lower():
                return row["id"]
        return None
    finally:
        conn.close()


def find_store_id(name: str) -> Optional[int]:
    """Find store ID by fuzzy name/city match."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT id, name, city FROM stores")
        for row in cursor.fetchall():
            if name.lower() in row["name"].lower() or name.lower() in row["city"].lower():
                return row["id"]
        return None
    finally:
        conn.close()


def find_category(name: str) -> Optional[str]:
    """Find category by name."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT DISTINCT category FROM products")
        categories = [row["category"] for row in cursor.fetchall()]
        for cat in categories:
            if name.lower() in cat.lower() or cat.lower() in name.lower():
                return cat
        return None
    finally:
        conn.close()


def execute_intent(intent: CopilotIntent) -> Dict[str, Any]:
    """Execute the deterministic analytics based on intent."""
    product_id = find_product_id(intent.product) if intent.product else None
    store_id = find_store_id(intent.store) if intent.store else None
    category = find_category(intent.category) if intent.category else None

    # Determine time window
    days_window = 30
    if intent.time_range:
        if "7" in intent.time_range:
            days_window = 7
        elif "30" in intent.time_range or "month" in intent.time_range:
            days_window = 30
        elif "90" in intent.time_range:
            days_window = 90

    result = {"intent": intent.intent, "filters": intent.model_dump()}

    if intent.intent == "stock_out":
        items = detect_stockout_risk(store_id=store_id, category=category,
                                     risk_level=RiskLevel.CRITICAL)
        items += detect_stockout_risk(store_id=store_id, category=category,
                                      risk_level=RiskLevel.HIGH)
        result["data"] = [item.model_dump() for item in items[:20]]
        result["summary"] = f"Found {len(items)} products at risk"

    elif intent.intent == "overstock":
        items = detect_overstock(store_id=store_id, category=category)
        result["data"] = [item.model_dump() for item in items[:20]]
        result["summary"] = f"Found {len(items)} overstocked products"

    elif intent.intent == "product_performance":
        if product_id:
            perf = get_product_performance(product_id, store_id=store_id)
            result["data"] = perf
            result["summary"] = f"Performance for product {intent.product}"
        else:
            result["data"] = []
            result["summary"] = "No product specified"

    elif intent.intent == "store_performance":
        if store_id:
            perf = get_store_performance(store_id)
            stores = compare_stores()
            result["data"] = {"store": perf, "all_stores": stores}
            result["summary"] = f"Performance for store {intent.store}"
        else:
            stores = compare_stores()
            result["data"] = {"all_stores": stores}
            result["summary"] = "All stores comparison"

    elif intent.intent == "sales_trend":
        trend = get_sales_trend(days_window, store_id=store_id, category=category)
        result["data"] = trend
        result["summary"] = f"Sales trend for last {days_window} days"

    elif intent.intent == "sales_anomaly":
        items = detect_sales_anomalies(store_id=store_id, category=category)
        result["data"] = [item.model_dump() for item in items[:20]]
        result["summary"] = f"Found {len(items)} sales anomalies"

    elif intent.intent == "recommendation":
        recs = generate_all_recommendations()
        if store_id:
            recs = [r for r in recs if r["store_id"] == store_id]
        if product_id:
            recs = [r for r in recs if r["product_id"] == product_id]
        result["data"] = recs[:20]
        result["summary"] = f"Generated {len(recs)} recommendations"

    elif intent.intent == "comparison":
        if intent.store and " and " in intent.store:
            # Compare two stores
            parts = intent.store.split(" and ")
            store1 = find_store_id(parts[0].strip())
            store2 = find_store_id(parts[1].strip())
            if store1 and store2:
                perf1 = get_store_performance(store1)
                perf2 = get_store_performance(store2)
                result["data"] = {"store1": perf1, "store2": perf2}
                result["summary"] = f"Comparison: {parts[0]} vs {parts[1]}"
            else:
                result["data"] = {}
                result["summary"] = "Could not find both stores"
        else:
            stores = compare_stores()
            result["data"] = {"all_stores": stores}
            result["summary"] = "All stores comparison"

    elif intent.intent == "inventory_status":
        inventory = get_current_inventory(store_id=store_id, product_id=product_id)
        result["data"] = inventory
        result["summary"] = f"Inventory status ({len(inventory)} items)"

    elif intent.intent == "general_data_question":
        # Return dashboard summary
        dashboard = get_dashboard_data()
        result["data"] = dashboard.model_dump()
        result["summary"] = "General dashboard overview"

    else:
        result["data"] = {}
        result["summary"] = "Unknown intent"

    return result


def process_copilot_query(question: str) -> Dict[str, Any]:
    """Main entry point for copilot query processing."""
    # Check if Gemini is configured
    if not gemini_client.is_configured():
        return {
            "answer": "AI Copilot is not configured. Please set GEMINI_API_KEY in .env file.",
            "evidence": "Gemini API key not found in environment.",
            "calculation": "",
            "recommendation": "Add GEMINI_API_KEY to .env and restart the application.",
            "assumptions": "Dashboard features work without Gemini.",
            "error": "GEMINI_API_KEY not configured"
        }

    # Extract intent
    intent = gemini_client.extract_intent(question)
    if not intent:
        return {
            "answer": "I couldn't understand your question. Please try rephrasing.",
            "evidence": "",
            "calculation": "",
            "recommendation": "Try questions like: 'What's running out?', 'What's overstocked?', 'How did laptops perform?'",
            "assumptions": "",
            "error": "Intent extraction failed"
        }

    # Validate intent
    valid_intents = [
        "stock_out", "overstock", "product_performance", "store_performance",
        "sales_trend", "sales_anomaly", "recommendation", "comparison",
        "inventory_status", "general_data_question", "unknown"
    ]
    if intent.intent not in valid_intents:
        intent.intent = "unknown"

    # Execute deterministic analytics
    try:
        result = execute_intent(intent)
    except Exception as e:
        return {
            "answer": f"Error processing your request: {str(e)}",
            "evidence": "",
            "calculation": "",
            "recommendation": "",
            "assumptions": "",
            "error": str(e)
        }

    # Handle empty results
    data = result.get("data", [])
    if isinstance(data, list) and len(data) == 0:
        return {
            "answer": f"No data found for your query: {result['summary']}",
            "evidence": "Database query returned no matching records.",
            "calculation": "",
            "recommendation": "Try adjusting your filters or time range.",
            "assumptions": "Data may not exist for the specified criteria.",
            "error": "No matching records"
        }

    # Generate explanation using Gemini
    explanation = gemini_client.explain_results(question, intent.intent, result)

    return explanation