from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    HEALTHY = "HEALTHY"
    NO_SALES = "NO_RECENT_SALES"


class ActionType(str, Enum):
    REORDER = "REORDER"
    PROMOTE = "PROMOTE"
    TRANSFER = "TRANSFER"
    INVESTIGATE = "INVESTIGATE"
    MONITOR = "MONITOR"
    NO_ACTION = "NO_ACTION"


class Priority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Store(BaseModel):
    id: int
    name: str
    city: str
    region: str


class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float
    cost: float
    reorder_threshold: int
    target_stock: int


class Sale(BaseModel):
    id: int
    date: str
    store_id: int
    product_id: int
    quantity: int
    revenue: float


class Inventory(BaseModel):
    id: int
    snapshot_date: str
    store_id: int
    product_id: int
    stock_quantity: int


class StockStatus(BaseModel):
    product_id: int
    product_name: str
    store_id: int
    store_name: str
    category: str
    current_stock: int
    avg_daily_sales: float
    days_remaining: Optional[float]
    risk_level: RiskLevel
    reorder_threshold: int


class OverstockItem(BaseModel):
    product_id: int
    product_name: str
    store_id: int
    store_name: str
    category: str
    current_stock: int
    avg_daily_sales: float
    days_inventory: float
    recent_sales_7d: int
    reason: str
    reorder_threshold: int


class SalesAnomaly(BaseModel):
    product_id: int
    product_name: str
    store_id: int
    store_name: str
    category: str
    anomaly_type: str  # SPIKE or DROP
    historical_avg: float
    recent_avg: float
    pct_change: float
    recent_sales_7d: int
    historical_sales_7d: int


class Recommendation(BaseModel):
    product_id: int
    product_name: str
    store_id: int
    store_name: str
    action: ActionType
    priority: Priority
    reason: str
    evidence: dict
    assumptions: List[str]


class DashboardKPIs(BaseModel):
    total_revenue: float
    total_units_sold: int
    inventory_value: float
    low_stock_count: int
    overstock_count: int
    attention_count: int


class DashboardData(BaseModel):
    kpis: DashboardKPIs
    sales_trend: List[dict]
    store_performance: List[dict]
    top_products: List[dict]
    inventory_health: List[dict]
    anomaly_summary: dict


class CopilotQuery(BaseModel):
    question: str


class CopilotIntent(BaseModel):
    intent: str
    product: Optional[str] = None
    store: Optional[str] = None
    category: Optional[str] = None
    time_range: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class CopilotResponse(BaseModel):
    answer: str
    evidence: Optional[str] = None
    calculation: Optional[str] = None
    recommendation: Optional[str] = None
    assumptions: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    database: str
    gemini_configured: bool