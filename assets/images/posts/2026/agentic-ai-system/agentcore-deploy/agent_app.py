"""AgentCore Runtime entry point for the e-commerce support agent."""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

# ── Tools (same as local version) ──

@tool
def track_order(order_id: str) -> dict:
    """Track the shipping status of an order."""
    # In production, this calls your order management API
    # For demo, returns simulated data
    return {
        "order_id": order_id,
        "status": "in_transit",
        "carrier": "FedEx",
        "tracking_number": "794644790132",
        "estimated_delivery": "2026-04-23",
    }

@tool
def check_payment_status(customer_id: str) -> dict:
    """Check payment history for a customer."""
    return {
        "customer_id": customer_id,
        "payments": [
            {"amount": 167.76, "status": "completed", "date": "2026-04-10"},
        ],
    }

@tool
def lookup_customer(customer_id: str) -> dict:
    """Look up customer profile."""
    return {
        "customer_id": customer_id,
        "name": "Demo Customer",
        "plan": "Premium",
        "loyalty_tier": "Gold",
    }

# ── Agent Setup ──

model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
)

agent = Agent(
    model=model,
    system_prompt="""You are a customer support agent for an e-commerce company.
Help customers with order tracking, billing questions, and account issues.
Use the available tools to look up real data before answering.""",
    tools=[track_order, check_payment_status, lookup_customer],
)

# ── AgentCore Entry Point ──

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """Process customer support requests."""
    prompt = payload.get("prompt", "Hello, how can I help?")
    customer_id = payload.get("customer_id", "unknown")

    full_prompt = f"Customer {customer_id} says: {prompt}"
    result = agent(full_prompt)

    return {
        "response": str(result),
        "customer_id": customer_id,
    }

if __name__ == "__main__":
    app.run()
