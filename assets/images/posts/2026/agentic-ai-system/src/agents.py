"""Specialized support agents for the e-commerce system.

Three domain agents + one supervisor that routes requests.
Each agent has its own tools, system prompt, and expertise.

Article 6 routed queries with Python keyword matching.
This article lets the agents reason about what to do.
"""

from __future__ import annotations

from strands import Agent
from strands.models import BedrockModel

from .tools import (
    track_order, lookup_order_history, cancel_order,
    check_payment_status, process_refund,
    lookup_customer, reset_password, update_account_info,
    check_service_status, escalate_to_human,
)


def create_model(region: str = "us-east-1") -> BedrockModel:
    """Create a Bedrock model for the agents."""
    return BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region_name=region,
    )


def create_order_agent(region: str = "us-east-1") -> Agent:
    """Create the Order Support Agent.

    Handles: order tracking, shipping status, cancellations, returns.
    """
    return Agent(
        model=create_model(region),
        system_prompt="""You are the Order Support Agent for an e-commerce company.

Your job is to help customers with order-related issues:
- Track packages and provide shipping updates
- Look up order history
- Process cancellations for unshipped orders
- Explain return policies for shipped/delivered orders

Always look up the order first before answering. Be specific with dates,
tracking numbers, and carrier information. If an order has an issue flagged
(like wrong item), acknowledge it proactively.

If you can't resolve the issue, escalate to a human agent with a clear summary.""",
        tools=[track_order, lookup_order_history, cancel_order,
               check_service_status, escalate_to_human],
    )


def create_billing_agent(region: str = "us-east-1") -> Agent:
    """Create the Billing Support Agent.

    Handles: payment inquiries, duplicate charges, refunds, pricing questions.
    """
    return Agent(
        model=create_model(region),
        system_prompt="""You are the Billing Support Agent for an e-commerce company.

Your job is to help customers with billing and payment issues:
- Check payment history and identify charges
- Detect and flag duplicate charges
- Process refunds (amounts over $50 require manager approval)
- Explain pricing and subscription details

Always check the payment records first. If you find a duplicate charge,
proactively offer a refund. Be transparent about refund timelines (3-5 business days).

For refunds over $50, explain that manager approval is required and the customer
will be notified within 24 hours. Never process unauthorized refunds.""",
        tools=[check_payment_status, process_refund, lookup_customer,
               check_service_status, escalate_to_human],
    )


def create_account_agent(region: str = "us-east-1") -> Agent:
    """Create the Account Support Agent.

    Handles: login issues, password resets, profile updates, account settings.
    """
    return Agent(
        model=create_model(region),
        system_prompt="""You are the Account Support Agent for an e-commerce company.

Your job is to help customers with account-related issues:
- Reset passwords and help with login problems
- Update account information (email, phone, address)
- Explain account features and loyalty tiers
- Troubleshoot app and website access issues

For password resets, always verify the customer ID first. For email changes,
explain that verification is required on both old and new email addresses.

If the customer reports a technical issue (app crashing, website errors),
check the service status first before troubleshooting.""",
        tools=[lookup_customer, reset_password, update_account_info,
               check_service_status, escalate_to_human],
    )


def create_supervisor_agent(region: str = "us-east-1") -> Agent:
    """Create the Supervisor Agent that routes requests.

    Analyzes the customer's message and decides which specialist to involve.
    For multi-issue requests, identifies all issues and routes to multiple agents.
    """
    return Agent(
        model=create_model(region),
        system_prompt="""You are the Supervisor Agent for an e-commerce customer support team.

Your job is to analyze incoming customer requests and route them to the right specialist:

ORDER AGENT — for: package tracking, shipping status, order cancellation, returns, wrong items
BILLING AGENT — for: payment questions, charges, refunds, duplicate charges, pricing
ACCOUNT AGENT — for: login issues, password resets, email/phone/address changes, app problems

Analyze the customer's message and respond with a JSON object:
{
    "agents": ["order", "billing", "account"],
    "reasoning": "Brief explanation of why these agents are needed",
    "priority": "low|medium|high|critical",
    "needs_human_review": true/false
}

Rules:
- A message can require multiple agents (e.g., "I was charged twice AND my package is late")
- Set priority to "high" if the customer mentions money issues or is clearly frustrated
- Set priority to "critical" if the customer threatens to cancel or mentions legal action
- Set needs_human_review to true for: refunds over $100, account security concerns, or angry customers
- Always include reasoning so the team can audit routing decisions""",
        tools=[lookup_customer],
    )
