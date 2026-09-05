import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from src.config import settings
from src.database import init_database, database_exists, get_table_counts
from src.analytics import (
    get_dashboard_data, detect_stockout_risk, detect_overstock,
    detect_sales_anomalies, get_all_stores, get_all_products,
    get_current_inventory, get_sales_trend, compare_stores,
    get_top_products, get_product_performance, get_store_performance,
    get_attention_items, RiskLevel
)
from src.recommendations import generate_all_recommendations
from src.copilot import process_copilot_query
from src.models import CopilotQuery, HealthResponse


class CachedStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs) -> Response:
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


app = FastAPI(
    title="RetailIQ API",
    description="AI Sales & Inventory Copilot for Retail Managers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    if not database_exists():
        init_database()


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    db_status = "connected" if database_exists() else "not_initialized"
    return HealthResponse(
        status="healthy",
        database=db_status,
        gemini_configured=bool(settings.gemini_api_key and settings.gemini_api_key != "")
    )


@app.get("/api/dashboard")
async def get_dashboard():
    return get_dashboard_data().model_dump()


@app.get("/api/stores")
async def list_stores():
    return get_all_stores()


@app.get("/api/products")
async def list_products(category: Optional[str] = None):
    products = get_all_products()
    if category:
        products = [p for p in products if p["category"] == category]
    return products


@app.get("/api/inventory")
async def get_inventory(
    store_id: Optional[int] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
    risk: Optional[str] = None
):
    inventory = get_current_inventory(store_id=store_id, product_id=product_id)

    if category:
        inventory = [i for i in inventory if i["category"] == category]

    if risk:
        risk_level = RiskLevel(risk.upper())
        risks = detect_stockout_risk(store_id=store_id, category=category, risk_level=risk_level)
        risk_product_store = {(r.product_id, r.store_id) for r in risks}
        inventory = [i for i in inventory if (i["product_id"], i["store_id"]) in risk_product_store]

    return inventory


@app.get("/api/sales")
async def get_sales(
    days: int = 30,
    store_id: Optional[int] = None,
    category: Optional[str] = None
):
    return get_sales_trend(days, store_id, category)


@app.get("/api/risks")
async def get_risks(
    store_id: Optional[int] = None,
    category: Optional[str] = None,
    level: Optional[str] = None
):
    risk_level = RiskLevel(level.upper()) if level else None
    risks = detect_stockout_risk(store_id=store_id, category=category, risk_level=risk_level)
    return [r.model_dump() for r in risks]


@app.get("/api/overstock")
async def get_overstock(
    store_id: Optional[int] = None,
    category: Optional[str] = None
):
    items = detect_overstock(store_id=store_id, category=category)
    return [item.model_dump() for item in items]


@app.get("/api/anomalies")
async def get_anomalies(
    store_id: Optional[int] = None,
    category: Optional[str] = None
):
    items = detect_sales_anomalies(store_id=store_id, category=category)
    return [item.model_dump() for item in items]


@app.get("/api/recommendations")
async def get_recommendations(
    store_id: Optional[int] = None,
    product_id: Optional[int] = None
):
    recs = generate_all_recommendations()
    if store_id:
        recs = [r for r in recs if r["store_id"] == store_id]
    if product_id:
        recs = [r for r in recs if r["product_id"] == product_id]
    return recs


@app.get("/api/attention")
async def get_attention():
    return get_attention_items()


@app.get("/api/products/top")
async def get_top_products_endpoint(limit: int = 10):
    return get_top_products(limit)


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    perf = get_product_performance(product_id)
    if not perf:
        raise HTTPException(status_code=404, detail="Product not found")
    return perf


@app.get("/api/stores/performance")
async def get_stores_performance():
    return compare_stores()


@app.get("/api/products/top")
async def get_top_products_endpoint(limit: int = 10):
    return get_top_products(limit)


@app.get("/api/stores/{store_id}")
async def get_store(store_id: int):
    perf = get_store_performance(store_id)
    if not perf:
        raise HTTPException(status_code=404, detail="Store not found")
    return perf


@app.post("/api/copilot/query")
async def copilot_query(query: CopilotQuery):
    result = process_copilot_query(query.question)
    return result


# Serve frontend
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", CachedStaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/favicon.svg")
    async def favicon():
        response = FileResponse(frontend_dist / "favicon.svg")
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    @app.get("/icons.svg")
    async def icons():
        response = FileResponse(frontend_dist / "icons.svg")
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            response = FileResponse(file_path)
            if full_path.startswith("assets/"):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return response
        response = FileResponse(frontend_dist / "index.html")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response
else:
    @app.get("/")
    async def root():
        return {"message": "RetailIQ API", "docs": "/docs", "frontend": "not built"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)