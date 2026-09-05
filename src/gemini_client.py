import os
import json
import google.generativeai as genai
from typing import Optional, Dict, Any
from src.config import settings
from src.models import CopilotIntent


class GeminiClient:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = None
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')

    def is_configured(self) -> bool:
        return self.api_key is not None and self.api_key != ""

    def extract_intent(self, question: str) -> Optional[CopilotIntent]:
        """Extract structured intent from user question."""
        if not self.is_configured() or not self.model:
            return None

        prompt = f"""You are an intent classifier for a retail inventory copilot.
Analyze the user's question and return a JSON object with the following structure:

{{
    "intent": "one of: stock_out, overstock, product_performance, store_performance, sales_trend, sales_anomaly, recommendation, comparison, inventory_status, general_data_question, unknown",
    "product": "product name if mentioned, otherwise null",
    "store": "store name/city if mentioned, otherwise null",
    "category": "category if mentioned, otherwise null",
    "time_range": "time range like '7_days', '30_days', 'this_month', 'last_month', otherwise null",
    "date_from": "YYYY-MM-DD if specific date mentioned, otherwise null",
    "date_to": "YYYY-MM-DD if specific date mentioned, otherwise null"
}}

Rules:
- Only extract explicit mentions, don't infer
- For "running out", "low stock", "stockout" -> intent: "stock_out"
- For "overstocked", "slow moving", "excess inventory" -> intent: "overstock"
- For "how did X perform", "performance of X" -> intent: "product_performance" or "store_performance"
- For "sales trend", "sales over time" -> intent: "sales_trend"
- For "spike", "drop", "unusual", "anomaly" -> intent: "sales_anomaly"
- For "what should I reorder", "recommendations" -> intent: "recommendation"
- For "compare X and Y" -> intent: "comparison"
- For "what's in stock", "inventory status" -> intent: "inventory_status"
- For general questions about data -> intent: "general_data_question"
- If unclear -> intent: "unknown"

User question: "{question}"

Return ONLY the JSON object, no extra text."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # Clean up markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            data = json.loads(text)
            return CopilotIntent(**data)
        except Exception as e:
            print(f"Intent extraction error: {e}")
            return None

    def explain_results(self, question: str, intent: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate evidence-first explanation from verified data."""
        if not self.is_configured() or not self.model:
            return {
                "answer": "AI explanation unavailable (Gemini not configured).",
                "evidence": str(data),
                "calculation": "",
                "recommendation": "",
                "assumptions": "Gemini API key not configured."
            }

        prompt = f"""You are a retail analytics assistant. Explain the following verified data to the store manager.

IMPORTANT RULES:
- These numbers are VERIFIED from the database. DO NOT change or invent any numbers.
- DO NOT add calculations not shown in the data.
- If data is empty or insufficient, SAY SO clearly.
- Structure your response with these sections: ANSWER, EVIDENCE, CALCULATION, RECOMMENDATION, ASSUMPTIONS
- Each section should be clear and concise.
- If a section doesn't apply, omit it.

User question: "{question}"
Intent: {intent}

Verified data:
{json.dumps(data, indent=2, default=str)}

Provide the explanation in this exact format:

## ANSWER
[Direct answer to the question using ONLY the verified numbers]

## EVIDENCE
[Key data points that support the answer]

## CALCULATION
[Show the math: e.g., "12 units / 8.1 units/day = 1.48 days"]

## RECOMMENDATION
[Actionable recommendation if applicable]

## ASSUMPTIONS
[Any assumptions made in the analysis]"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Parse sections
            sections = {
                "answer": "",
                "evidence": "",
                "calculation": "",
                "recommendation": "",
                "assumptions": ""
            }

            current_section = None
            for line in text.split("\n"):
                line_stripped = line.strip()
                if line_stripped.startswith("## ANSWER"):
                    current_section = "answer"
                elif line_stripped.startswith("## EVIDENCE"):
                    current_section = "evidence"
                elif line_stripped.startswith("## CALCULATION"):
                    current_section = "calculation"
                elif line_stripped.startswith("## RECOMMENDATION"):
                    current_section = "recommendation"
                elif line_stripped.startswith("## ASSUMPTIONS"):
                    current_section = "assumptions"
                elif current_section and line_stripped:
                    sections[current_section] += line + "\n"

            # Clean up trailing newlines
            for k in sections:
                sections[k] = sections[k].strip()

            return sections
        except Exception as e:
            print(f"Explanation generation error: {e}")
            return {
                "answer": "Unable to generate AI explanation.",
                "evidence": str(data),
                "calculation": "",
                "recommendation": "",
                "assumptions": f"Error: {str(e)}"
            }


gemini_client = GeminiClient()