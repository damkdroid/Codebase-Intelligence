
from typing import List, Dict, Any
from sample_project.config import load_settings, format_iso_timestamp
from sample_project.database import DatabaseClient


def calculate_cart_subtotal(items: List[Dict[str, Any]]) -> float:
    return sum(float(item.get("price", 0.0)) * int(item.get("quantity", 1)) for item in items)


def apply_discount_code(subtotal: float, discount_code: str = "") -> float:
    code = (discount_code or "").strip().upper()
    if code == "SUMMER20":
        return subtotal * 0.80
    elif code == "VIP10":
        return subtotal * 0.90
    elif code == "FLAT5":
        return max(0.0, subtotal - 5.0)
    return subtotal


def compute_sales_tax(taxable_amount: float) -> float:
    settings = load_settings()
    tax_rate = float(settings.get("tax_rate", 0.0825))
    return round(taxable_amount * tax_rate, 2)


def process_order_checkout(
    db: DatabaseClient,
    user_id: int,
    items: List[Dict[str, Any]],
    discount_code: str = ""
) -> Dict[str, Any]:
    subtotal = calculate_cart_subtotal(items)
    discounted = apply_discount_code(subtotal, discount_code)
    tax = compute_sales_tax(discounted)
    total = round(discounted + tax, 2)

    created_at = format_iso_timestamp()
    query = "INSERT INTO orders (user_id, total_amount, status, created_at) VALUES (?, ?, ?, ?)"
    db.execute_query(query, (user_id, total, "completed", created_at))

    return {
        "user_id": user_id,
        "subtotal": subtotal,
        "discounted_amount": discounted,
        "tax": tax,
        "total_amount": total,
        "status": "completed",
        "created_at": created_at,
    }
