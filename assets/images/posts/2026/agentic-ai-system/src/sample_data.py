"""Sample e-commerce data for the multi-agent support system.

Simulates a mid-size e-commerce company's backend systems:
orders, customers, payments, and shipping.
"""

from datetime import datetime, timedelta

# Customer profiles
CUSTOMERS = {
    "CUST-1001": {
        "name": "Sarah Chen",
        "email": "sarah.chen@email.com",
        "phone": "512-555-0142",
        "plan": "Premium",
        "member_since": "2024-03-15",
        "address": "742 Evergreen Terrace, Austin, TX 78701",
        "lifetime_orders": 47,
        "lifetime_spend": 3842.50,
        "loyalty_tier": "Gold",
    },
    "CUST-1002": {
        "name": "James Wilson",
        "email": "j.wilson@email.com",
        "phone": "512-555-0198",
        "plan": "Standard",
        "member_since": "2025-01-10",
        "address": "123 Oak Street, Round Rock, TX 78664",
        "lifetime_orders": 8,
        "lifetime_spend": 412.00,
        "loyalty_tier": "Bronze",
    },
    "CUST-1003": {
        "name": "Maria Garcia",
        "email": "maria.g@email.com",
        "phone": "512-555-0267",
        "plan": "Premium",
        "member_since": "2023-06-01",
        "address": "456 Cedar Lane, Georgetown, TX 78626",
        "lifetime_orders": 92,
        "lifetime_spend": 8150.75,
        "loyalty_tier": "Platinum",
    },
}

# Order history
ORDERS = {
    "ORD-50421": {
        "customer_id": "CUST-1001",
        "date": "2026-04-15",
        "items": [
            {"name": "Wireless Noise-Canceling Headphones", "sku": "ELEC-HP-200", "qty": 1, "price": 149.99},
            {"name": "USB-C Charging Cable (6ft)", "sku": "ACC-CB-010", "qty": 2, "price": 12.99},
        ],
        "subtotal": 175.97,
        "shipping": 0.00,
        "tax": 14.52,
        "total": 190.49,
        "status": "delivered",
        "shipping_carrier": "UPS",
        "tracking_number": "1Z999AA10123456784",
        "shipped_date": "2026-04-16",
        "delivered_date": "2026-04-19",
    },
    "ORD-50435": {
        "customer_id": "CUST-1001",
        "date": "2026-04-18",
        "items": [
            {"name": "Ergonomic Standing Desk Mat", "sku": "HOME-DM-050", "qty": 1, "price": 79.99},
        ],
        "subtotal": 79.99,
        "shipping": 5.99,
        "tax": 6.60,
        "total": 92.58,
        "status": "in_transit",
        "shipping_carrier": "FedEx",
        "tracking_number": "794644790132",
        "shipped_date": "2026-04-19",
        "estimated_delivery": "2026-04-23",
    },
    "ORD-50440": {
        "customer_id": "CUST-1002",
        "date": "2026-04-17",
        "items": [
            {"name": "Bluetooth Portable Speaker", "sku": "ELEC-SP-100", "qty": 1, "price": 59.99},
            {"name": "Waterproof Phone Case", "sku": "ACC-PC-020", "qty": 1, "price": 24.99},
        ],
        "subtotal": 84.98,
        "shipping": 5.99,
        "tax": 7.01,
        "total": 97.98,
        "status": "processing",
        "shipping_carrier": None,
        "tracking_number": None,
        "shipped_date": None,
        "estimated_delivery": "2026-04-24",
    },
    "ORD-50398": {
        "customer_id": "CUST-1003",
        "date": "2026-04-10",
        "items": [
            {"name": "Premium Yoga Mat", "sku": "FIT-YM-300", "qty": 1, "price": 89.99},
            {"name": "Resistance Band Set", "sku": "FIT-RB-100", "qty": 1, "price": 34.99},
            {"name": "Foam Roller", "sku": "FIT-FR-050", "qty": 1, "price": 29.99},
        ],
        "subtotal": 154.97,
        "shipping": 0.00,
        "tax": 12.79,
        "total": 167.76,
        "status": "delivered",
        "shipping_carrier": "USPS",
        "tracking_number": "9400111899223100001234",
        "shipped_date": "2026-04-11",
        "delivered_date": "2026-04-14",
        "issue": "wrong_item",
        "issue_detail": "Received blue yoga mat instead of purple (ordered FIT-YM-300-PUR)",
    },
    "ORD-50445": {
        "customer_id": "CUST-1003",
        "date": "2026-04-19",
        "items": [
            {"name": "Smart Water Bottle", "sku": "FIT-WB-200", "qty": 2, "price": 44.99},
        ],
        "subtotal": 89.98,
        "shipping": 0.00,
        "tax": 7.42,
        "total": 97.40,
        "status": "shipped",
        "shipping_carrier": "UPS",
        "tracking_number": "1Z999AA10123456799",
        "shipped_date": "2026-04-20",
        "estimated_delivery": "2026-04-22",
    },
}

# Payment records
PAYMENTS = {
    "PAY-8001": {
        "customer_id": "CUST-1001",
        "order_id": "ORD-50421",
        "amount": 190.49,
        "method": "Visa ending 4242",
        "date": "2026-04-15",
        "status": "completed",
    },
    "PAY-8002": {
        "customer_id": "CUST-1001",
        "order_id": "ORD-50435",
        "amount": 92.58,
        "method": "Visa ending 4242",
        "date": "2026-04-18",
        "status": "completed",
    },
    "PAY-8003": {
        "customer_id": "CUST-1002",
        "order_id": "ORD-50440",
        "amount": 97.98,
        "method": "Mastercard ending 5555",
        "date": "2026-04-17",
        "status": "completed",
    },
    "PAY-8004": {
        "customer_id": "CUST-1003",
        "order_id": "ORD-50398",
        "amount": 167.76,
        "method": "Amex ending 1234",
        "date": "2026-04-10",
        "status": "completed",
    },
    "PAY-8004-DUP": {
        "customer_id": "CUST-1003",
        "order_id": "ORD-50398",
        "amount": 167.76,
        "method": "Amex ending 1234",
        "date": "2026-04-10",
        "status": "completed",
        "flag": "duplicate_charge",
    },
    "PAY-8005": {
        "customer_id": "CUST-1003",
        "order_id": "ORD-50445",
        "amount": 97.40,
        "method": "Amex ending 1234",
        "date": "2026-04-19",
        "status": "completed",
    },
}

# Service status
SERVICE_STATUS = {
    "website": {"status": "operational", "uptime": "99.98%", "response_time_ms": 120},
    "checkout": {"status": "operational", "uptime": "99.99%", "response_time_ms": 340},
    "payments": {"status": "operational", "uptime": "99.99%", "response_time_ms": 200},
    "shipping_api": {"status": "degraded", "uptime": "98.5%", "response_time_ms": 2100,
                      "incident": "Carrier API experiencing intermittent timeouts since 2:00 PM CT"},
    "mobile_app": {"status": "operational", "uptime": "99.9%", "response_time_ms": 180},
    "search": {"status": "operational", "uptime": "99.95%", "response_time_ms": 95},
}
