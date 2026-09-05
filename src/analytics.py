import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from src.config import settings
from src.database import get_connection
from src.models import (
    RiskLevel, StockStatus, OverstockItem, SalesAnomaly,
    DashboardKPIs, DashboardData
)


def get_db():
    return get_connection()


# ==================== BASIC QUERIES ====================

def get_total_revenue(date_from: Optional[str] = None, date_to: Optional[str] = None,
                      store_id: Optional[int] = None) -> float:
    conn = get_db()
    try:
        query = "SELECT SUM(revenue) as total FROM sales WHERE 1=1"
        params = []
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        if store_id:
            query += " AND store_id = ?"
            params.append(store_id)
        cursor = conn.execute(query, params)
        result = cursor.fetchone()
        return result["total"] or 0.0
    finally:
        conn.close()


def get_total_units_sold(date_from: Optional[str] = None, date_to: Optional[str] = None,
                         store_id: Optional[int] = None) -> int:
    conn = get_db()
    try:
        query = "SELECT SUM(quantity) as total FROM sales WHERE 1=1"
        params = []
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        if store_id:
            query += " AND store_id = ?"
            params.append(store_id)
        cursor = conn.execute(query, params)
        result = cursor.fetchone()
        return result["total"] or 0
    finally:
        conn.close()


def get_inventory_value() -> float:
    conn = get_db()
    try:
        query = """
            SELECT SUM(i.stock_quantity * p.cost) as total_value
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
        """
        cursor = conn.execute(query)
        result = cursor.fetchone()
        return result["total_value"] or 0.0
    finally:
        conn.close()


def get_current_inventory(store_id: Optional[int] = None, product_id: Optional[int] = None) -> List[Dict]:
    conn = get_db()
    try:
        query = """
            SELECT i.*, p.name as product_name, p.category, p.price, p.cost,
                   p.reorder_threshold, p.target_stock, s.name as store_name
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            JOIN stores s ON i.store_id = s.id
            WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
        """
        params = []
        if store_id:
            query += " AND i.store_id = ?"
            params.append(store_id)
        if product_id:
            query += " AND i.product_id = ?"
            params.append(product_id)
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_stores() -> List[Dict]:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM stores")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_products() -> List[Dict]:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM products")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_product_by_id(product_id: int) -> Optional[Dict]:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_store_by_id(store_id: int) -> Optional[Dict]:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM stores WHERE id = ?", (store_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ==================== AVERAGE DAILY SALES ====================

def calculate_average_daily_sales(product_id: int, store_id: int,
                                  days: int = 30, date_to: Optional[str] = None) -> float:
    """Calculate average daily sales for a product/store over the last N days."""
    conn = get_db()
    try:
        if date_to is None:
            cursor = conn.execute("SELECT MAX(date) as max_date FROM sales")
            date_to = cursor.fetchone()["max_date"]

        date_from = (datetime.strptime(date_to, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")

        query = """
            SELECT COALESCE(SUM(quantity), 0) as total_qty
            FROM sales
            WHERE product_id = ? AND store_id = ? AND date >= ? AND date <= ?
        """
        cursor = conn.execute(query, (product_id, store_id, date_from, date_to))
        result = cursor.fetchone()
        total_qty = result["total_qty"] or 0
        return total_qty / days if days > 0 else 0.0
    finally:
        conn.close()


def get_recent_sales(product_id: int, store_id: int, days: int = 7,
                     date_to: Optional[str] = None) -> int:
    """Get total sales quantity in the last N days."""
    conn = get_db()
    try:
        if date_to is None:
            cursor = conn.execute("SELECT MAX(date) as max_date FROM sales")
            date_to = cursor.fetchone()["max_date"]

        date_from = (datetime.strptime(date_to, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")

        query = """
            SELECT COALESCE(SUM(quantity), 0) as total_qty
            FROM sales
            WHERE product_id = ? AND store_id = ? AND date >= ? AND date <= ?
        """
        cursor = conn.execute(query, (product_id, store_id, date_from, date_to))
        result = cursor.fetchone()
        return result["total_qty"] or 0
    finally:
        conn.close()


def get_historical_avg_sales(product_id: int, store_id: int, days: int = 30,
                             date_to: Optional[str] = None, exclude_recent_days: int = 7) -> float:
    """Get historical average daily sales excluding recent period."""
    conn = get_db()
    try:
        if date_to is None:
            cursor = conn.execute("SELECT MAX(date) as max_date FROM sales")
            date_to = cursor.fetchone()["max_date"]

        recent_start = (datetime.strptime(date_to, "%Y-%m-%d") - timedelta(days=exclude_recent_days)).strftime("%Y-%m-%d")
        historical_start = (datetime.strptime(date_to, "%Y-%m-%d") - timedelta(days=days + exclude_recent_days)).strftime("%Y-%m-%d")

        query = """
            SELECT COALESCE(SUM(quantity), 0) as total_qty
            FROM sales
            WHERE product_id = ? AND store_id = ? AND date >= ? AND date < ?
        """
        cursor = conn.execute(query, (product_id, store_id, historical_start, recent_start))
        result = cursor.fetchone()
        total_qty = result["total_qty"] or 0
        return total_qty / days if days > 0 else 0.0
    finally:
        conn.close()


# ==================== STOCK-OUT RISK ====================

def calculate_days_of_stock(current_stock: int, avg_daily_sales: float) -> Optional[float]:
    if avg_daily_sales <= 0:
        return None
    return current_stock / avg_daily_sales


def classify_risk_level(days_remaining: Optional[float]) -> RiskLevel:
    if days_remaining is None:
        return RiskLevel.NO_SALES
    if days_remaining <= 3:
        return RiskLevel.CRITICAL
    elif days_remaining <= 7:
        return RiskLevel.HIGH
    elif days_remaining <= 14:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HEALTHY


def detect_stockout_risk(store_id: Optional[int] = None, category: Optional[str] = None,
                         risk_level: Optional[RiskLevel] = None, days_window: int = 30) -> List[StockStatus]:
    conn = get_db()
    try:
        query = """
            SELECT i.stock_quantity, p.id as product_id, p.name as product_name, p.category,
                   p.reorder_threshold, s.id as store_id, s.name as store_name
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            JOIN stores s ON i.store_id = s.id
            WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
        """
        params = []
        if store_id:
            query += " AND i.store_id = ?"
            params.append(store_id)
        if category:
            query += " AND p.category = ?"
            params.append(category)

        cursor = conn.execute(query, params)
        inventory_rows = [dict(row) for row in cursor.fetchall()]

        results = []
        for row in inventory_rows:
            pid = row["product_id"]
            sid = row["store_id"]
            avg_daily = calculate_average_daily_sales(pid, sid, days_window)
            days_rem = calculate_days_of_stock(row["stock_quantity"], avg_daily)
            risk = classify_risk_level(days_rem)

            if risk_level and risk != risk_level:
                continue

            results.append(StockStatus(
                product_id=pid,
                product_name=row["product_name"],
                store_id=sid,
                store_name=row["store_name"],
                category=row["category"],
                current_stock=row["stock_quantity"],
                avg_daily_sales=round(avg_daily, 2),
                days_remaining=round(days_rem, 2) if days_rem else None,
                risk_level=risk,
                reorder_threshold=row["reorder_threshold"]
            ))

        # Sort by risk level priority and days remaining
        risk_order = {RiskLevel.CRITICAL: 0, RiskLevel.HIGH: 1, RiskLevel.MEDIUM: 2,
                      RiskLevel.NO_SALES: 3, RiskLevel.HEALTHY: 4}
        results.sort(key=lambda x: (risk_order[x.risk_level], x.days_remaining or 999))
        return results
    finally:
        conn.close()


# ==================== OVERSTOCK DETECTION ====================

def detect_overstock(store_id: Optional[int] = None, category: Optional[str] = None,
                     days_threshold: int = 45, days_window: int = 30) -> List[OverstockItem]:
    conn = get_db()
    try:
        query = """
            SELECT i.stock_quantity, p.id as product_id, p.name as product_name, p.category,
                   p.reorder_threshold, s.id as store_id, s.name as store_name
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            JOIN stores s ON i.store_id = s.id
            WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM inventory)
        """
        params = []
        if store_id:
            query += " AND i.store_id = ?"
            params.append(store_id)
        if category:
            query += " AND p.category = ?"
            params.append(category)

        cursor = conn.execute(query, params)
        inventory_rows = [dict(row) for row in cursor.fetchall()]

        results = []
        for row in inventory_rows:
            pid = row["product_id"]
            sid = row["store_id"]
            avg_daily = calculate_average_daily_sales(pid, sid, days_window)
            recent_sales = get_recent_sales(pid, sid, 7)

            if avg_daily <= 0:
                days_inventory = 999.0 if row["stock_quantity"] > 0 else 0.0
            else:
                days_inventory = row["stock_quantity"] / avg_daily

            # Overstock: high inventory AND low sales velocity
            if days_inventory > days_threshold and avg_daily < 1.0:
                reason = f"High inventory ({row['stock_quantity']} units) with low sales velocity ({avg_daily:.2f}/day)"
            elif days_inventory > days_threshold * 1.5:
                reason = f"Very high days of inventory ({days_inventory:.1f} days)"
            else:
                continue

            results.append(OverstockItem(
                product_id=pid,
                product_name=row["product_name"],
                store_id=sid,
                store_name=row["store_name"],
                category=row["category"],
                current_stock=row["stock_quantity"],
                avg_daily_sales=round(avg_daily, 2),
                days_inventory=round(days_inventory, 1),
                recent_sales_7d=recent_sales,
                reason=reason,
                reorder_threshold=row["reorder_threshold"]
            ))

        results.sort(key=lambda x: x.days_inventory, reverse=True)
        return results
    finally:
        conn.close()


# ==================== SALES ANOMALIES ====================

def detect_sales_anomalies(store_id: Optional[int] = None, category: Optional[str] = None,
                           days_window: int = 30, recent_days: int = 7,
                           spike_threshold: float = 0.5, drop_threshold: float = -0.5) -> List[SalesAnomaly]:
    conn = get_db()
    try:
        query = """
            SELECT p.id as product_id, p.name as product_name, p.category,
                   s.id as store_id, s.name as store_name
            FROM products p
            CROSS JOIN stores s
            WHERE 1=1
        """
        params = []
        if store_id:
            query += " AND s.id = ?"
            params.append(store_id)
        if category:
            query += " AND p.category = ?"
            params.append(category)

        cursor = conn.execute(query, params)
        product_store_pairs = [dict(row) for row in cursor.fetchall()]

        results = []
        for pair in product_store_pairs:
            pid = pair["product_id"]
            sid = pair["store_id"]

            historical_avg = get_historical_avg_sales(pid, sid, days_window, exclude_recent_days=recent_days)
            recent_avg = calculate_average_daily_sales(pid, sid, recent_days)

            if historical_avg <= 0 and recent_avg <= 0:
                continue

            if historical_avg > 0:
                pct_change = (recent_avg - historical_avg) / historical_avg
            else:
                pct_change = 1.0 if recent_avg > 0 else 0.0

            anomaly_type = None
            if pct_change >= spike_threshold:
                anomaly_type = "SPIKE"
            elif pct_change <= drop_threshold:
                anomaly_type = "DROP"
            else:
                continue

            recent_sales = get_recent_sales(pid, sid, recent_days)
            historical_sales = int(historical_avg * recent_days)

            results.append(SalesAnomaly(
                product_id=pid,
                product_name=pair["product_name"],
                store_id=sid,
                store_name=pair["store_name"],
                category=pair["category"],
                anomaly_type=anomaly_type,
                historical_avg=round(historical_avg, 2),
                recent_avg=round(recent_avg, 2),
                pct_change=round(pct_change * 100, 1),
                recent_sales_7d=recent_sales,
                historical_sales_7d=historical_sales
            ))

        results.sort(key=lambda x: abs(x.pct_change), reverse=True)
        return results
    finally:
        conn.close()


# ==================== TOP/BOTTOM PRODUCTS ====================

def get_top_products(limit: int = 10, date_from: Optional[str] = None,
                     date_to: Optional[str] = None, store_id: Optional[int] = None) -> List[Dict]:
    conn = get_db()
    try:
        query = """
            SELECT p.id, p.name, p.category,
                   SUM(sa.quantity) as total_qty,
                   SUM(sa.revenue) as total_revenue
            FROM sales sa
            JOIN products p ON sa.product_id = p.id
            WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND sa.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND sa.date <= ?"
            params.append(date_to)
        if store_id:
            query += " AND sa.store_id = ?"
            params.append(store_id)

        query += " GROUP BY p.id, p.name, p.category ORDER BY total_revenue DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_bottom_products(limit: int = 10, date_from: Optional[str] = None,
                        date_to: Optional[str] = None, store_id: Optional[int] = None) -> List[Dict]:
    conn = get_db()
    try:
        query = """
            SELECT p.id, p.name, p.category,
                   SUM(sa.quantity) as total_qty,
                   SUM(sa.revenue) as total_revenue
            FROM sales sa
            JOIN products p ON sa.product_id = p.id
            WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND sa.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND sa.date <= ?"
            params.append(date_to)
        if store_id:
            query += " AND sa.store_id = ?"
            params.append(store_id)

        query += " GROUP BY p.id, p.name, p.category ORDER BY total_revenue ASC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ==================== STORE PERFORMANCE ====================

def compare_stores(date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict]:
    conn = get_db()
    try:
        query = """
            SELECT st.id, st.name, st.city,
                   COALESCE(SUM(sa.quantity), 0) as units_sold,
                   COALESCE(SUM(sa.revenue), 0) as revenue,
                   COUNT(DISTINCT sa.product_id) as products_sold
            FROM stores st
            LEFT JOIN sales sa ON st.id = sa.store_id
            WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND sa.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND sa.date <= ?"
            params.append(date_to)

        query += " GROUP BY st.id, st.name, st.city ORDER BY revenue DESC"
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_store_performance(store_id: int, date_from: Optional[str] = None,
                          date_to: Optional[str] = None) -> Dict:
    conn = get_db()
    try:
        query = """
            SELECT COALESCE(SUM(sa.quantity), 0) as units_sold,
                   COALESCE(SUM(sa.revenue), 0) as revenue,
                   COUNT(DISTINCT sa.product_id) as products_sold
            FROM sales sa
            WHERE sa.store_id = ?
        """
        params = [store_id]
        if date_from:
            query += " AND sa.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND sa.date <= ?"
            params.append(date_to)

        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


# ==================== PRODUCT PERFORMANCE ====================

def get_product_performance(product_id: int, date_from: Optional[str] = None,
                            date_to: Optional[str] = None, store_id: Optional[int] = None) -> Dict:
    conn = get_db()
    try:
        query = """
            SELECT p.id, p.name, p.category, p.price,
                   COALESCE(SUM(sa.quantity), 0) as units_sold,
                   COALESCE(SUM(sa.revenue), 0) as revenue
            FROM sales sa
            JOIN products p ON sa.product_id = p.id
            WHERE sa.product_id = ?
        """
        params = [product_id]
        if date_from:
            query += " AND sa.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND sa.date <= ?"
            params.append(date_to)
        if store_id:
            query += " AND sa.store_id = ?"
            params.append(store_id)

        query += " GROUP BY p.id, p.name, p.category, p.price"
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


# ==================== SALES TREND ====================

def get_sales_trend(days: int = 30, store_id: Optional[int] = None,
                    category: Optional[str] = None) -> List[Dict]:
    conn = get_db()
    try:
        cursor = conn.execute("SELECT MAX(date) as max_date FROM sales")
        max_date = cursor.fetchone()["max_date"]
        date_from = (datetime.strptime(max_date, "%Y-%m-%d") - timedelta(days=days - 1)).strftime("%Y-%m-%d")

        query = """
            SELECT sa.date,
                   SUM(sa.quantity) as units,
                   SUM(sa.revenue) as revenue
            FROM sales sa
            JOIN products p ON sa.product_id = p.id
            WHERE sa.date >= ? AND sa.date <= ?
        """
        params = [date_from, max_date]
        if store_id:
            query += " AND sa.store_id = ?"
            params.append(store_id)
        if category:
            query += " AND p.category = ?"
            params.append(category)

        query += " GROUP BY sa.date ORDER BY sa.date"
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ==================== DASHBOARD ====================

def get_dashboard_data() -> DashboardData:
    # KPIs
    kpis = DashboardKPIs(
        total_revenue=round(get_total_revenue(), 2),
        total_units_sold=get_total_units_sold(),
        inventory_value=round(get_inventory_value(), 2),
        low_stock_count=len(detect_stockout_risk(risk_level=RiskLevel.CRITICAL)),
        overstock_count=len(detect_overstock()),
        attention_count=len(detect_stockout_risk(risk_level=RiskLevel.CRITICAL)) +
                        len(detect_stockout_risk(risk_level=RiskLevel.HIGH)) +
                        len(detect_overstock()) +
                        len(detect_sales_anomalies())
    )

    # Sales trend (last 30 days)
    sales_trend = get_sales_trend(30)

    # Store performance
    store_perf = compare_stores()

    # Top products
    top_products = get_top_products(10)

    # Inventory health distribution
    all_risks = detect_stockout_risk()
    health_dist = defaultdict(int)
    for r in all_risks:
        health_dist[r.risk_level.value] += 1
    inventory_health = [{"risk_level": k, "count": v} for k, v in health_dist.items()]

    # Anomaly summary
    anomalies = detect_sales_anomalies()
    anomaly_summary = {
        "spike_count": sum(1 for a in anomalies if a.anomaly_type == "SPIKE"),
        "drop_count": sum(1 for a in anomalies if a.anomaly_type == "DROP"),
        "total": len(anomalies)
    }

    return DashboardData(
        kpis=kpis,
        sales_trend=sales_trend,
        store_performance=store_perf,
        top_products=top_products,
        inventory_health=inventory_health,
        anomaly_summary=anomaly_summary
    )


# ==================== ATTENTION ITEMS ====================

def get_attention_items() -> Dict:
    """Get all items needing attention grouped by severity."""
    critical_risks = detect_stockout_risk(risk_level=RiskLevel.CRITICAL)
    high_risks = detect_stockout_risk(risk_level=RiskLevel.HIGH)
    overstock = detect_overstock()
    anomalies = detect_sales_anomalies()

    return {
        "critical": [r.model_dump() for r in critical_risks],
        "high": [r.model_dump() for r in high_risks],
        "overstock": [o.model_dump() for o in overstock],
        "anomalies": [a.model_dump() for a in anomalies]
    }