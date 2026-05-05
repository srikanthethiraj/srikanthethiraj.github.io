"""Amazon Bedrock AgentCore — production deployment.

Takes the Strands agent and deploys it to AgentCore Runtime.
AgentCore handles compute, scaling, memory, identity, and observability.

This is the "production deployment" step:
- Strands = build the agent (code-first, custom tools)
- AgentCore = run it at scale (managed infrastructure)
"""

from __future__ import annotations

import json
import os


def create_agentcore_app_code() -> str:
    """Generate the AgentCore app code for deployment.

    This creates the entry point file that AgentCore Runtime expects.
    The @app.entrypoint decorator wraps the Strands agent as an HTTP service.
    """
    code = '''"""AgentCore Runtime entry point for the e-commerce support agent."""

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
'''
    return code


def create_agentcore_requirements() -> str:
    """Generate requirements.txt for AgentCore deployment."""
    return """strands-agents>=1.0.0
bedrock-agentcore
"""


def create_agentcore_dockerfile() -> str:
    """Generate Dockerfile for AgentCore custom deployment."""
    return """FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent_app.py .

EXPOSE 8080

CMD ["python", "agent_app.py"]
"""


def write_agentcore_files(output_dir: str) -> dict:
    """Write all AgentCore deployment files to a directory.

    Args:
        output_dir: Directory to write files to.

    Returns:
        Dict with file paths created.
    """
    os.makedirs(output_dir, exist_ok=True)

    files = {
        "agent_app.py": create_agentcore_app_code(),
        "requirements.txt": create_agentcore_requirements(),
        "Dockerfile": create_agentcore_dockerfile(),
    }

    paths = {}
    for filename, content in files.items():
        path = os.path.join(output_dir, filename)
        with open(path, "w") as f:
            f.write(content)
        paths[filename] = path

    return paths


def demo_harness_concept():
    """Demonstrate the AgentCore Managed Harness concept.

    Shows how to declare and deploy an agent with config only — no orchestration code.
    The harness is in preview (US West, US East, Sydney, Frankfurt).
    """
    print("\n   AgentCore Managed Harness (Preview):")
    print("   ─────────────────────────────────────")
    print()
    print("   Deploy an agent in 3 API calls — no orchestration code:")
    print()
    print("   Step 1: Create the agent")
    print("   ┌──────────────────────────────────────────────────────┐")
    print("   │  agentcore.create_agent(                             │")
    print("   │      name='order-support',                           │")
    print("   │      model='us.anthropic.claude-sonnet-4-20250514',  │")
    print("   │      instructions='You are an order support agent.', │")
    print("   │      tools=[track_order, lookup_history],            │")
    print("   │  )                                                   │")
    print("   └──────────────────────────────────────────────────────┘")
    print()
    print("   Step 2: Invoke the agent")
    print("   ┌──────────────────────────────────────────────────────┐")
    print("   │  agentcore.invoke_agent(                             │")
    print("   │      agent_name='order-support',                     │")
    print("   │      prompt='Where is my order ORD-50435?',          │")
    print("   │  )                                                   │")
    print("   └──────────────────────────────────────────────────────┘")
    print()
    print("   Step 3: Iterate — swap model or add tools via config")
    print("   ┌──────────────────────────────────────────────────────┐")
    print("   │  agentcore.update_agent(                             │")
    print("   │      name='order-support',                           │")
    print("   │      model='us.anthropic.claude-haiku-4-...',        │")
    print("   │      tools=[track_order, lookup_history, cancel],    │")
    print("   │  )                                                   │")
    print("   └──────────────────────────────────────────────────────┘")
    print()
    print("   What the harness handles automatically:")
    print("   ✅ Compute — microVM isolation per invocation")
    print("   ✅ Tooling — tool registration and execution")
    print("   ✅ Memory — durable session state (suspend/resume)")
    print("   ✅ Identity — IAM roles and security")
    print("   ✅ Orchestration — powered by Strands under the hood")
    print()
    print("   ⚠️  Limitation: the harness deploys a single agent.")
    print("   For multi-agent orchestration (supervisor + specialists),")
    print("   you need AgentCore + custom code (Phase 6).")
    print()
    print("   Available in preview: us-west-2, us-east-1, ap-southeast-2, eu-central-1")

    return {
        "mode": "managed_harness",
        "api_calls": 3,
        "status": "preview",
        "regions": ["us-west-2", "us-east-1", "ap-southeast-2", "eu-central-1"],
    }


def demo_agentcore_concept():
    """Demonstrate the AgentCore deployment concept locally.

    Shows the deployment pattern and files without actually deploying.
    """
    print("\n   AgentCore Deployment Pattern:")
    print("   ─────────────────────────────")
    print()
    print("   Your Strands Agent (code-first)")
    print("        │")
    print("        ▼")
    print("   @app.entrypoint decorator (bedrock-agentcore SDK)")
    print("        │")
    print("        ▼")
    print("   HTTP service on port 8080")
    print("        │")
    print("        ▼")
    print("   AgentCore Runtime (managed compute, scaling, identity)")
    print()

    print("   Deployment options:")
    print("   1. Starter Toolkit — pip install bedrock-agentcore-starter-toolkit")
    print("      → agentcore deploy (one command)")
    print("   2. AgentCore CLI — agentcore create-runtime → agentcore deploy")
    print("   3. Custom Docker — build image, push to ECR, deploy to AgentCore")
    print()

    print("   What AgentCore manages for you:")
    print("   ✅ Compute — auto-scaling based on request volume")
    print("   ✅ Identity — IAM roles scoped per agent")
    print("   ✅ Memory — persistent session state across invocations")
    print("   ✅ Observability — CloudWatch traces, metrics, logs")
    print("   ✅ Networking — VPC integration, private endpoints")
    print()

    print("   Local testing:")
    print("   $ python agent_app.py")
    print("   $ curl -X POST http://localhost:8080/invocations \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"prompt": "Where is my order?", "customer_id": "CUST-1001"}\'')
    print()

    print("   Deploy to AgentCore:")
    print("   $ pip install bedrock-agentcore-starter-toolkit")
    print("   $ agentcore deploy --agent-name ecommerce-support")

    return {
        "entry_point": "agent_app.py",
        "sdk": "bedrock-agentcore",
        "port": 8080,
        "deploy_command": "agentcore deploy --agent-name ecommerce-support",
    }
