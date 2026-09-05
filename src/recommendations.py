from typing import List, Dict, Optional
from src.models import ActionType, Priority, RiskLevel
from src.analytics import (
    calculate_average_daily_sales, calculate_days_of_stock,
    classify_risk_level, detect_stockout_risk, detect_overstock,
    detect_sales_anomalies
)
from src.config import settings
from src.database import get_connection


def get_transfer_opportunities() -> List[Dict]:
    """Find stores where one has overstock and another has stock-out risk for same product."""
    conn = get_connection()
    try:
        # Get all overstock items
        overstock_items = detect_overstock()
        # Get all critical/high risk items
        risk_items = detect_stockout_risk(risk_level=RiskLevel.CRITICAL) + \
                     detect_stockout_risk(risk_level=RiskLevel.HIGH)

        opportunities = []
        for over in overstock_items:
            for risk in risk_items:
                if over.product_id == risk.product_id and over.store_id != risk.store_id:
                    # Check if overstock store has enough to share
                    if over.current_stock > over.reorder_threshold * 2:
                        opportunities.append({
                            "product_id": over.product_id,
                            "product_name": over.product_name,
                            "from_store_id": over.store_id,
                            "from_store_name": over.store_name,
                            "from_stock": over.current_stock,
                            "to_store_id": risk.store_id,
                            "to_store_name": risk.store_name,
                            "to_stock": risk.current_stock,
                            "to_days_remaining": risk.days_remaining,
                            "suggested_transfer_qty": min(
                                over.current_stock - over.reorder_threshold,
                                risk.reorder_threshold * 2
                            )
                        })
        return opportunities
    finally:
        conn.close()


def generate_recommendation_for_stockout(item, risk_level: RiskLevel) -> Dict:
    """Generate recommendation for stock-out risk item."""
    avg_daily = item.avg_daily_sales
    days_rem = item.days_remaining
    current = item.current_stock

    days_str = f"{days_rem:.1f}" if days_rem is not None else "N/A (no recent sales)"

    if risk_level == RiskLevel.CRITICAL:
        action = ActionType.REORDER
        priority = Priority.CRITICAL
        reason = f"CRITICAL: Only {days_str} days of stock remaining at current sales rate ({avg_daily:.1f}/day)"
    elif risk_level == RiskLevel.HIGH:
        action = ActionType.REORDER
        priority = Priority.HIGH
        reason = f"HIGH: {days_str} days of stock remaining at current sales rate ({avg_daily:.1f}/day)"
    else:
        action = ActionType.MONITOR
        priority = Priority.MEDIUM
        reason = f"MEDIUM: {days_str} days of stock remaining"

    # Check for transfer opportunity
    transfer_opps = get_transfer_opportunities()
    for opp in transfer_opps:
        if opp["product_id"] == item.product_id and opp["to_store_id"] == item.store_id:
            action = ActionType.TRANSFER
            reason += f". Transfer possible from {opp['from_store_name']} (has {opp['from_stock']} units)."
            break

    return {
        "product_id": item.product_id,
        "product_name": item.product_name,
        "store_id": item.store_id,
        "store_name": item.store_name,
        "action": action,
        "priority": priority,
        "reason": reason,
        "evidence": {
            "current_stock": current,
            "avg_daily_sales": avg_daily,
            "days_remaining": days_rem,
            "risk_level": risk_level.value,
            "reorder_threshold": item.reorder_threshold
        },
        "assumptions": [
            f"Sales velocity based on last 30-day average ({avg_daily:.2f} units/day)",
            "No incoming shipments considered",
            "Demand pattern assumed to remain stable"
        ]
    }


def generate_recommendation_for_overstock(item) -> Dict:
    """Generate recommendation for overstocked item."""
    avg_daily = item.avg_daily_sales
    days_inv = item.days_inventory
    current = item.current_stock

    if days_inv > 90 and avg_daily < 0.5:
        action = ActionType.PROMOTE
        priority = Priority.HIGH
        reason = f"SEVERE OVERSTOCK: {days_inv:.0f} days of inventory with very low sales ({avg_daily:.2f}/day). Consider promotion or markdown."
    elif days_inv > 60:
        action = ActionType.PROMOTE
        priority = Priority.MEDIUM
        reason = f"OVERSTOCK: {days_inv:.0f} days of inventory with low sales ({avg_daily:.2f}/day). Consider promotional activity."
    else:
        action = ActionType.MONITOR
        priority = Priority.LOW
        reason = f"ELEVATED INVENTORY: {days_inv:.0f} days of inventory. Monitor sales velocity."

    return {
        "product_id": item.product_id,
        "product_name": item.product_name,
        "store_id": item.store_id,
        "store_name": item.store_name,
        "action": action,
        "priority": priority,
        "reason": reason,
        "evidence": {
            "current_stock": current,
            "avg_daily_sales": avg_daily,
            "days_inventory": days_inv,
            "recent_sales_7d": item.recent_sales_7d
        },
        "assumptions": [
            f"Sales velocity based on last 30-day average ({avg_daily:.2f} units/day)",
            "No seasonality adjustments applied",
            "Promotion effectiveness not modeled"
        ]
    }


def generate_recommendation_for_anomaly(anomaly) -> Dict:
    """Generate recommendation for sales anomaly."""
    pct = anomaly.pct_change
    anomaly_type = anomaly.anomaly_type

    if anomaly_type == "SPIKE":
        if pct > 100:
            priority = Priority.HIGH
            reason = f"SIGNIFICANT SPIKE: Sales increased {pct:.0f}% vs historical average. Investigate cause (promotion, event, competitor stockout?)."
        else:
            priority = Priority.MEDIUM
            reason = f"MODERATE SPIKE: Sales increased {pct:.0f}% vs historical average. Monitor for sustainability."
    else:  # DROP
        if pct < -70:
            priority = Priority.HIGH
            reason = f"SIGNIFICANT DROP: Sales decreased {abs(pct):.0f}% vs historical average. Investigate cause (stockout, quality issue, competitor?)."
        else:
            priority = Priority.MEDIUM
            reason = f"MODERATE DROP: Sales decreased {abs(pct):.0f}% vs historical average. Monitor for recovery."

    return {
        "product_id": anomaly.product_id,
        "product_name": anomaly.product_name,
        "store_id": anomaly.store_id,
        "store_name": anomaly.store_name,
        "action": ActionType.INVESTIGATE,
        "priority": priority,
        "reason": reason,
        "evidence": {
            "anomaly_type": anomaly_type,
            "historical_avg_daily": anomaly.historical_avg,
            "recent_avg_daily": anomaly.recent_avg,
            "pct_change": pct,
            "recent_sales_7d": anomaly.recent_sales_7d,
            "historical_sales_7d": anomaly.historical_sales_7d
        },
        "assumptions": [
            f"Historical baseline: {anomaly.historical_avg:.2f} units/day (30-day avg excluding last 7 days)",
            f"Recent period: {anomaly.recent_avg:.2f} units/day (last 7 days)",
            "External factors (holidays, promotions) not automatically detected"
        ]
    }


def generate_all_recommendations(limit_per_category: int = 10) -> List[Dict]:
    """Generate all recommendations across all categories."""
    recommendations = []

    # Stock-out recommendations (limit to top items)
    critical_risks = detect_stockout_risk(risk_level=RiskLevel.CRITICAL)[:limit_per_category]
    for item in critical_risks:
        recommendations.append(generate_recommendation_for_stockout(item, RiskLevel.CRITICAL))

    high_risks = detect_stockout_risk(risk_level=RiskLevel.HIGH)[:limit_per_category]
    for item in high_risks:
        recommendations.append(generate_recommendation_for_stockout(item, RiskLevel.HIGH))

    # Overstock recommendations
    overstock_items = detect_overstock()[:limit_per_category]
    for item in overstock_items:
        recommendations.append(generate_recommendation_for_overstock(item))

    # Anomaly recommendations
    anomalies = detect_sales_anomalies()[:limit_per_category]
    for anomaly in anomalies:
        recommendations.append(generate_recommendation_for_anomaly(anomaly))

    # Sort by priority
    priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 999))

    return recommendations