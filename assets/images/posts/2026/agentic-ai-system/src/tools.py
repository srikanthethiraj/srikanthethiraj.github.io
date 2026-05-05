"""E-commerce support tools for the multi-agent system.

Each tool connects to a simulated backend system. In production,
these would call real APIs — Shopify, Stripe, ShipStation, etc.
The agent decides which tools to use based on the customer's request.
"""

from __future__ import annotations

from datetime import datetime
from strands import tool

from .sample_data import CUSTOMERS, ORDERS, PAYMENTS, SERVICE_STATUS


# ── Order Tools (used by the Order Agent) ──

@tool
def track_order(order_id: str) -> dict:
    """Track the shipping status of an order.

    Args:
        order_id: The order ID (e.g., ORD-50421).

    Returns:
        Shipping status, carrier, tracking number, and estimated delivery.
    """
    order = ORDERS.get(order_id)
    if not order:
        return {"error": f"Order {order_id} not found"}

    return {
        "order_id": order_id,
        "status": order["status"],
        "carrier": order.get("shipping_carrier"),
        "tracking_number": order.get("tracking_number"),
        "shipped_date": order.get("shipped_date"),
        "delivered_date": order.get("delivered_date"),
        "estimated_delivery": order.get("estimated_delivery"),
        "items": [item["name"] for item in order["items"]],
    }


@tool
def lookup_order_history(customer_id: str) -> dict:
    """Look up all orders for a customer.

    Args:
        customer_id: The customer ID (e.g., CUST-1001).

    Returns:
        List of recent orders with status and totals.
    """
    customer_orders = [
        {
            "order_id": oid,
            "date": o["date"],
            "total": o["total"],
            "status": o["status"],
            "items": [item["name"] for item in o["items"]],
            "issue": o.get("issue"),
        }
        for oid, o in ORDERS.items()
        if o["customer_id"] == customer_id
    ]

    if not customer_orders:
        return {"error": f"No orders found for {customer_id}"}

    return {"customer_id": customer_id, "orders": customer_orders}


@tool
def cancel_order(order_id: str) -> dict:
    """Cancel an order if it hasn't shipped yet.

    Args:
        order_id: The order ID to cancel.

    Returns:
        Cancellation confirmation or rejection reason.
    """
    order = ORDERS.get(order_id)
    if not order:
        return {"error": f"Order {order_id} not found"}

    if order["status"] in ("delivered", "shipped", "in_transit"):
        return {
            "status": "cannot_cancel",
            "reason": f"Order is already {order['status']}. Please request a return instead.",
            "order_id": order_id,
        }

    return {
        "status": "cancelled",
        "order_id": order_id,
        "refund_amount": order["total"],
        "message": f"Order {order_id} cancelled. Refund of ${order['total']:.2f} will be processed in 3-5 business days.",
    }


# ── Billing Tools (used by the Billing Agent) ──

@tool
def check_payment_status(customer_id: str) -> dict:
    """Check all payments and charges for a customer.

    Args:
        customer_id: The customer ID.

    Returns:
        List of payments with amounts, dates, and any flagged issues.
    """
    customer_payments = [
        {
            "payment_id": pid,
            "order_id": p["order_id"],
            "amount": p["amount"],
            "method": p["method"],
            "date": p["date"],
            "status": p["status"],
            "flag": p.get("flag"),
        }
        for pid, p in PAYMENTS.items()
        if p["customer_id"] == customer_id
    ]

    if not customer_payments:
        return {"error": f"No payments found for {customer_id}"}

    flagged = [p for p in customer_payments if p.get("flag")]
    return {
        "customer_id": customer_id,
        "payments": customer_payments,
        "flagged_issues": flagged,
        "total_charged": sum(p["amount"] for p in customer_payments),
    }


@tool
def process_refund(customer_id: str, order_id: str, amount: float, reason: str) -> dict:
    """Process a refund for a customer. Amounts over $50 require human approval.

    Args:
        customer_id: The customer ID.
        order_id: The order ID to refund.
        amount: Refund amount in dollars.
        reason: Reason for the refund.

    Returns:
        Refund confirmation or approval request.
    """
    if amount > 50:
        return {
            "status": "pending_approval",
            "message": f"Refund of ${amount:.2f} requires manager approval (threshold: $50).",
            "customer_id": customer_id,
            "order_id": order_id,
            "reason": reason,
            "approval_required": True,
        }

    return {
        "status": "approved",
        "refund_id": f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "customer_id": customer_id,
        "order_id": order_id,
        "amount": amount,
        "reason": reason,
        "message": f"Refund of ${amount:.2f} processed. Will appear on statement in 3-5 business days.",
    }


# ── Account Tools (used by the Account Agent) ──

@tool
def lookup_customer(customer_id: str) -> dict:
    """Look up customer profile information.

    Args:
        customer_id: The customer ID.

    Returns:
        Customer profile with name, plan, loyalty tier, and account details.
    """
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    return {"customer_id": customer_id, **customer}


@tool
def reset_password(customer_id: str) -> dict:
    """Send a password reset email to the customer.

    Args:
        customer_id: The customer ID.

    Returns:
        Confirmation that the reset email was sent.
    """
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    return {
        "status": "sent",
        "message": f"Password reset email sent to {customer['email']}. Link expires in 24 hours.",
        "customer_id": customer_id,
    }


@tool
def update_account_info(customer_id: str, field: str, new_value: str) -> dict:
    """Update customer account information. Email changes require verification.

    Args:
        customer_id: The customer ID.
        field: The field to update (email, phone, address).
        new_value: The new value for the field.

    Returns:
        Update confirmation or verification request.
    """
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    if field == "email":
        return {
            "status": "verification_required",
            "message": f"Verification email sent to both {customer['email']} and {new_value}. Please confirm within 48 hours.",
            "customer_id": customer_id,
        }

    return {
        "status": "updated",
        "customer_id": customer_id,
        "field": field,
        "old_value": customer.get(field, "unknown"),
        "new_value": new_value,
        "message": f"{field.capitalize()} updated successfully.",
    }


# ── System Tools (used by any agent) ──

@tool
def check_service_status(service: str) -> dict:
    """Check if a service is operational.

    Args:
        service: Service name (website, checkout, payments, shipping_api, mobile_app, search).

    Returns:
        Service status, uptime, and any active incidents.
    """
    status = SERVICE_STATUS.get(service.lower())
    if not status:
        return {
            "error": f"Unknown service: {service}",
            "available_services": list(SERVICE_STATUS.keys()),
        }
    return {"service": service, "checked_at": datetime.now().isoformat(), **status}


@tool
def escalate_to_human(customer_id: str, summary: str, priority: str = "medium") -> dict:
    """Escalate a case to a human support agent.

    Args:
        customer_id: The customer ID.
        summary: Brief summary of the issue for the human agent.
        priority: Priority level (low, medium, high, critical).

    Returns:
        Escalation confirmation with ticket number.
    """
    return {
        "status": "escalated",
        "ticket_id": f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "customer_id": customer_id,
        "summary": summary,
        "priority": priority,
        "estimated_response": "15 minutes" if priority in ("high", "critical") else "2 hours",
    }
