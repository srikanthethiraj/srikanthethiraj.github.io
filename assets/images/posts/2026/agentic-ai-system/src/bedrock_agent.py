"""Bedrock Agents — managed prototype using InvokeInlineAgent.

Creates an order tracking agent using the inline agent API.
No Lambda functions, no IAM roles, no pre-created agent resources.
The agent reasons about the query, selects tools, and returns control
to your code for fulfillment.

Comparison to Strands:
- Faster to set up (single API call, no framework code)
- Less flexible (can't customize the orchestration loop)
- Tool calls are round-trips (return control → fulfill → resume)
- Good for simple, single-purpose agents
"""

from __future__ import annotations

import json
import uuid

import boto3
from botocore.exceptions import ClientError

from .sample_data import ORDERS


# ── Tool definitions for the inline agent ──

TOOL_FUNCTIONS = {
    "functions": [
        {
            "name": "TrackOrder",
            "description": "Look up the shipping status of an order by order ID",
            "parameters": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID (e.g., ORD-50435)",
                    "required": True,
                }
            },
        },
        {
            "name": "LookupOrderHistory",
            "description": "Get all orders for a customer by customer ID",
            "parameters": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID (e.g., CUST-1001)",
                    "required": True,
                }
            },
        },
    ]
}


def _fulfill_tool_call(function_name: str, parameters: dict) -> str:
    """Fulfill a tool call from the inline agent using local sample data.

    Args:
        function_name: The tool the agent wants to call.
        parameters: Parameters extracted by the agent.

    Returns:
        JSON string with the tool result.
    """
    if function_name == "TrackOrder":
        order_id = parameters.get("order_id", "")
        order = ORDERS.get(order_id)
        if not order:
            return json.dumps({"error": f"Order {order_id} not found"})
        return json.dumps({
            "order_id": order_id,
            "status": order["status"],
            "carrier": order.get("shipping_carrier"),
            "tracking_number": order.get("tracking_number"),
            "estimated_delivery": order.get("estimated_delivery"),
            "items": [item["name"] for item in order["items"]],
        })

    if function_name == "LookupOrderHistory":
        customer_id = parameters.get("customer_id", "")
        customer_orders = [
            {"order_id": oid, "status": o["status"], "total": o["total"]}
            for oid, o in ORDERS.items()
            if o["customer_id"] == customer_id
        ]
        if not customer_orders:
            return json.dumps({"error": f"No orders found for {customer_id}"})
        return json.dumps({"customer_id": customer_id, "orders": customer_orders})

    return json.dumps({"error": f"Unknown function: {function_name}"})


def demo_bedrock_inline_agent(region: str = "us-east-1") -> dict:
    """Run a real Bedrock Inline Agent demo with return-of-control.

    Creates an inline agent on the fly, sends a query, fulfills tool calls,
    and returns the final response. No pre-created agent resources needed.

    Args:
        region: AWS region.

    Returns:
        Dict with the agent's response and metadata.
    """
    client = boto3.client("bedrock-agent-runtime", region_name=region)
    session_id = str(uuid.uuid4())
    query = "Where is my order ORD-50435? When will it arrive?"

    print(f"\n   Customer: {query}")
    print(f"   Invoking Bedrock Inline Agent...")

    action_groups = [
        {
            "actionGroupName": "OrderTracking",
            "actionGroupExecutor": {"customControl": "RETURN_CONTROL"},
            "functionSchema": TOOL_FUNCTIONS,
        }
    ]

    try:
        # Step 1: Send query to inline agent
        response = client.invoke_inline_agent(
            sessionId=session_id,
            inputText=query,
            foundationModel="anthropic.claude-sonnet-4-20250514-v1:0",
            instruction=(
                "You are an order support agent for an e-commerce company. "
                "Help customers track packages and check order status. "
                "Always use the TrackOrder tool to look up real data before answering. "
                "Be specific with tracking numbers, carriers, and delivery dates."
            ),
            actionGroups=action_groups,
            enableTrace=True,
        )

        # Process the streaming response
        final_text = ""
        return_control = None

        for event in response.get("completion", []):
            if "chunk" in event:
                chunk_bytes = event["chunk"].get("bytes", b"")
                final_text += chunk_bytes.decode("utf-8")
            if "returnControl" in event:
                return_control = event["returnControl"]

        # Step 2: If agent wants to call a tool, fulfill it
        if return_control:
            invocation_id = return_control.get("invocationId", "")
            invocation_inputs = return_control.get("invocationInputs", [])

            for inv_input in invocation_inputs:
                func_inv = inv_input.get("functionInvocationInput", {})
                func_name = func_inv.get("function", "")
                params = {
                    p["name"]: p["value"]
                    for p in func_inv.get("parameters", [])
                }

                print(f"   Agent selected tool: {func_name}({params})")
                tool_result = _fulfill_tool_call(func_name, params)
                print(f"   Tool result: {tool_result[:200]}...")

                # Step 3: Send tool result back to agent
                resume_response = client.invoke_inline_agent(
                    sessionId=session_id,
                    inputText="",
                    foundationModel="anthropic.claude-sonnet-4-20250514-v1:0",
                    instruction=(
                        "You are an order support agent for an e-commerce company. "
                        "Help customers track packages and check order status."
                    ),
                    actionGroups=action_groups,
                    inlineSessionState={
                        "returnControlInvocationResults": [
                            {
                                "functionResult": {
                                    "actionGroup": "OrderTracking",
                                    "function": func_name,
                                    "responseBody": {
                                        "TEXT": {"body": tool_result}
                                    },
                                }
                            }
                        ],
                        "invocationId": invocation_id,
                    },
                )

                # Process final response
                final_text = ""
                for event in resume_response.get("completion", []):
                    if "chunk" in event:
                        chunk_bytes = event["chunk"].get("bytes", b"")
                        final_text += chunk_bytes.decode("utf-8")

        print(f"\n   Bedrock Agent: {final_text[:500]}")

        return {
            "response": final_text,
            "session_id": session_id,
            "tool_calls": len(return_control.get("invocationInputs", [])) if return_control else 0,
        }

    except ClientError as exc:
        error_msg = str(exc)
        print(f"\n   ⚠️  Bedrock Inline Agent error: {error_msg}")
        print("   (This requires bedrock:InvokeInlineAgent permission)")
        return {"error": error_msg}


# Keep the old concept demo as a fallback reference
def demo_bedrock_agent_concept():
    """Fallback: show the Bedrock Agent pattern if InvokeInlineAgent isn't available."""
    print("\n   Bedrock Agent Configuration (managed prototype):")
    print("   ─────────────────────────────────────────────────")
    config = {
        "foundationModel": "anthropic.claude-sonnet-4-20250514-v1:0",
        "instruction": "You are an order support agent...",
        "actionGroups": ["TrackOrder", "LookupOrderHistory", "CancelOrder"],
        "executionType": "RETURN_CONTROL (no Lambda needed)",
    }
    for k, v in config.items():
        print(f"   {k}: {v}")
    return config
