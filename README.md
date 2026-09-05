TRACK_ID=PS03

# RetailIQ — AI Sales & Inventory Copilot

## Problem Statement

A store manager's data is rich, but their decisions are rushed. Important information is buried across sales reports and stock sheets. RetailIQ is a copilot for store managers running small retail operations with multiple stores, a product catalogue, daily sales, and stock/inventory data.

## What the Application Does

RetailIQ provides:
- **Real-time dashboard** with KPIs, charts, and attention alerts
- **AI Copilot** that answers natural language questions using verified data
- **Evidence-first explanations** — every answer shows the actual numbers behind it
- **Deterministic analytics** — business calculations never depend on LLM hallucination
- **Stock-out prediction** — identifies products running out before they do
- **Overstock detection** — finds slow-moving inventory tying up capital
- **Sales anomaly detection** — spots meaningful spikes and drops
- **Actionable recommendations** — with priority, reason, evidence, and assumptions

## Main Features

1. **Dashboard** — Revenue, units sold, inventory value, low stock, overstock, needs attention
2. **Inventory Management** — Search, filter, risk assessment, days of stock remaining
3. **Sales Analytics** — Trends, store comparison, product ranking, anomaly detection
4. **Alerts** — Stock-out, overstock, sales spikes, sales drops with severity
5. **Recommendations** — Grouped by priority with full evidence trail
6. **AI Copilot** — Natural language queries with grounded, evidence-first responses

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Frontend      │────▶│   FastAPI        │────▶│   SQLite         │
│   (React/Vite)  │     │   Backend        │     │   Database       │
└─────────────────┘     └────────┬─────────┘     └──────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
           ┌─────────────────┐      ┌──────────────────┐
           │ Deterministic   │      │  Gemini Client   │
           │ Analytics       │      │  (Intent +       │
           │ Engine (Python) │      │   Explanation)   │
           └─────────────────┘      └──────────────────┘
```

## AI Architecture

**Critical principle: The LLM never calculates business values.**

1. **User Question** → Gemini interprets intent (structured JSON)
2. **Validated Intent** → Python deterministic functions execute
3. **SQLite** → Verified results returned
4. **Gemini** → Explains results using only provided numbers
5. **Response** → ANSWER, EVIDENCE, CALCULATION, RECOMMENDATION, ASSUMPTIONS

Supported intents: `stock_out`, `overstock`, `product_performance`, `store_performance`, `sales_trend`, `sales_anomaly`, `recommendation`, `comparison`, `inventory_status`, `general_data_question`, `unknown`

## Deterministic Analytics

All business logic is implemented in Python (`src/analytics.py`):

- **Stock-out risk**: `days_remaining = current_stock / avg_daily_sales`
  - CRITICAL: 0-3 days, HIGH: 4-7, MEDIUM: 8-14, HEALTHY: 15+
  - Zero sales handled separately ("No recent sales")
- **Overstock**: Days of inventory > 45 with low sales velocity
- **Sales anomalies**: Recent 7-day avg vs historical avg, >50% change = SPIKE/DROP
- **Recommendations**: Rule-based (REORDER, PROMOTE, TRANSFER, INVESTIGATE, MONITOR, NO_ACTION)

## Dataset Description

Synthetic but realistic retail data:
- **6 stores**: Hyderabad, Vijayawada, Visakhapatnam, Bengaluru, Chennai, Pune
- **80 products** across 7 categories (Electronics, Mobile Accessories, Computing, Home Appliances, Office Supplies, Personal Care, Accessories)
- **90 days** of daily sales data
- **Current inventory** snapshot
- Intentionally seeded scenarios: stock-out risk, overstock, sales spike, sales drop, top/bottom performers, strong/weak stores

## Folder Structure

```
retailiq/
├── app.py                 # Entry point
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py          # Settings
│   ├── database.py        # SQLite connection & init
│   ├── models.py          # Pydantic models
│   ├── analytics.py       # Deterministic business logic
│   ├── rules.py           # Recommendation rules
│   ├── recommendations.py # Recommendation engine
│   ├── copilot.py         # Copilot orchestration
│   ├── gemini_client.py   # Gemini API wrapper
│   ├── prompts.py         # Prompt templates
│   ├── api.py             # FastAPI routes
│   └── utils.py           # Helpers
├── data/
│   ├── stores.csv
│   ├── products.csv
│   ├── sales.csv
│   ├── inventory.csv
│   └── generate_data.py   # Data generation script
├── db/
│   └── retail.db          # SQLite database (created at runtime)
├── tests/
│   ├── test_database.py
│   ├── test_analytics.py
│   ├── test_rules.py
│   ├── test_api.py
│   └── test_copilot.py
└── frontend/              # React + Vite (built files committed)
    ├── src/
    ├── public/
    └── dist/
```

## Installation

```bash
# Clone and enter
cd retailiq

# Install Python dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the application
python app.py
```

The application will be available at **http://localhost:8000**

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes* | Google Gemini API key for AI features |
| `DATABASE_PATH` | No | Path to SQLite database (default: `db/retail.db`) |
| `API_HOST` | No | Host to bind (default: `0.0.0.0`) |
| `API_PORT` | No | Port to bind (default: `8000`) |

*Dashboard works without Gemini key; AI Copilot requires it.

## How to Run

```bash
# One command startup
pip install -r requirements.txt && python app.py
```

Then open http://localhost:8000

## Example Questions for AI Copilot

- "What's running out?"
- "What's overstocked?"
- "How did laptops perform this month?"
- "Which store performed best?"
- "What should I reorder today?"
- "Which products had sales drops?"
- "Compare Hyderabad and Vijayawada"
- "Why is Wireless Mouse high priority?"
- "What will sales be next year?" (tests refusal)

## Demo Workflow

1. Open dashboard — see KPIs, charts, attention section
2. Click "Needs Attention" — view stock-out, overstock, anomalies
3. Open AI Copilot — ask "What's running out?"
4. Show evidence — "Python calculated this, not the AI"
5. Ask "What should I reorder?" — see full recommendation with evidence
6. Ask "What's overstocked?" — see slow-moving products
7. Ask "Which products had unusual sales drops?" — see anomaly evidence
8. Ask "What will sales be next year?" — see disciplined refusal

## Failure Handling

- **Missing Gemini key**: Dashboard works, Copilot returns helpful message
- **Gemini timeout/unavailable**: Graceful degradation, deterministic features unaffected
- **Malformed LLM output**: Retry once with stricter prompt, then safe error
- **Empty results**: Clear "no matching data" messages
- **Zero division**: Handled explicitly in analytics
- **Invalid input**: Pydantic validation with clear error responses

## Known Limitations

- No forecasting model (intentionally — refuses future predictions)
- No real-time inventory sync (snapshot-based)
- No multi-user authentication (single-manager focus)
- No purchase order generation (recommendation only)
- Synthetic dataset (demo purposes only)
- English-only natural language support

## Demo Video Link Placeholder

[Demo Video :- https://drive.google.com/file/d/1_4twq9Q8jOS8Lb6RjRwKCyVJ97TebHOM/view?usp=sharing]
[youtube link :- https://youtu.be/MofjSNCtScI]

## Future Improvements

- CSV/Excel data upload
- Date-range comparison views
- Category-level analytics
- Downloadable PDF reports
- Natural language filters
- Executive summary generation
- Inventory transfer suggestions between stores
- Basic trend projections (with clear uncertainty bounds)
- Multi-user roles and permissions
- Real-time POS integration
