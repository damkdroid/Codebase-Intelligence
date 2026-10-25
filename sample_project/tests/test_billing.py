"""Tests for billing and discount calculations."""

from sample_project.billing import calculate_cart_subtotal, apply_discount_code, compute_sales_tax


def test_cart_subtotal_calculation():
    """Verify item subtotal matches quantity times price."""
    items = [
        {"name": "Widget A", "price": 10.0, "quantity": 2},
        {"name": "Widget B", "price": 25.0, "quantity": 1},
    ]
    subtotal = calculate_cart_subtotal(items)
    assert subtotal == 45.0


def test_discount_code_application():
    """Verify promotional code reductions."""
    subtotal = 100.0
    assert apply_discount_code(subtotal, "SUMMER20") == 80.0
    assert apply_discount_code(subtotal, "VIP10") == 90.0
    assert apply_discount_code(subtotal, "FLAT5") == 95.0
    assert apply_discount_code(subtotal, "INVALID") == 100.0
