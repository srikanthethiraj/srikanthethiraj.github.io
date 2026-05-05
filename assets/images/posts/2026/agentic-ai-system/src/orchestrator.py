"""Multi-agent orchestrator for the e-commerce support system.

Routes customer requests to specialized agents and combines responses.
Handles multi-issue requests by delegating to multiple agents.
"""

from __future__ import annotations

import json
import re
import time

from .agents import (
    create_order_agent,
    create_billing_agent,
    create_account_agent,
    create_supervisor_agent,
)
from .models import AgentResponse, RoutingDecision, HumanReviewRequest


class SupportOrchestrator:
    """Orchestrates multi-agent customer support."""

    def __init__(self, region: str = "us-east-1") -> None:
        self._region = region
        self._supervisor = create_supervisor_agent(region)
        self._agents = {
            "order": create_order_agent(region),
            "billing": create_billing_agent(region),
            "account": create_account_agent(region),
        }

    def handle_request(self, customer_id: str, message: str) -> dict:
        """Handle a customer support request end-to-end.

        1. Supervisor analyzes and routes the request
        2. Specialist agent(s) handle their part
        3. Responses are combined into a unified reply
        """
        start = time.monotonic()

        # Step 1: Route
        print(f"   🔀 Supervisor analyzing request...")
        routing = self._route_request(customer_id, message)
        print(f"   Routing: {routing.target_agent} (reason: {routing.reason})")

        if routing.needs_human_review:
            print(f"   ⚠️  Flagged for human review")

        # Step 2: Delegate to specialist(s)
        agent_names = [a.strip() for a in routing.target_agent.split(",")]
        responses = []

        for agent_name in agent_names:
            agent = self._agents.get(agent_name)
            if not agent:
                print(f"   ⚠️  Unknown agent: {agent_name}, skipping")
                continue

            print(f"   🤖 {agent_name.capitalize()} Agent working...")
            agent_start = time.monotonic()

            prompt = f"Customer {customer_id} says: {message}"
            try:
                result = agent(prompt)
                response_text = str(result)
                agent_latency = (time.monotonic() - agent_start) * 1000

                responses.append(AgentResponse(
                    agent_name=agent_name,
                    response=response_text,
                    latency_ms=agent_latency,
                ))
                print(f"   ✅ {agent_name.capitalize()} Agent done ({agent_latency:.0f}ms)")
            except Exception as exc:
                print(f"   ❌ {agent_name.capitalize()} Agent failed: {exc}")
                responses.append(AgentResponse(
                    agent_name=agent_name,
                    response=f"I'm sorry, I encountered an issue handling the {agent_name} part of your request. Let me escalate this to a human agent.",
                    latency_ms=0,
                ))

        total_latency = (time.monotonic() - start) * 1000

        return {
            "customer_id": customer_id,
            "routing": {
                "agents": agent_names,
                "reason": routing.reason,
                "priority": "high" if routing.needs_human_review else "medium",
                "needs_human_review": routing.needs_human_review,
            },
            "responses": [
                {"agent": r.agent_name, "response": r.response, "latency_ms": r.latency_ms}
                for r in responses
            ],
            "total_latency_ms": total_latency,
        }

    def _route_request(self, customer_id: str, message: str) -> RoutingDecision:
        """Use the supervisor agent to route the request."""
        prompt = f"Customer {customer_id} says: \"{message}\"\n\nRoute this request."

        try:
            result = self._supervisor(prompt)
            result_text = str(result)

            # Try to parse JSON from the supervisor's response
            json_match = re.search(r"\{[^{}]*\}", result_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                agents = parsed.get("agents", ["account"])
                return RoutingDecision(
                    target_agent=",".join(agents),
                    reason=parsed.get("reasoning", "Supervisor routing"),
                    confidence=0.9,
                    needs_human_review=parsed.get("needs_human_review", False),
                )
        except Exception as exc:
            print(f"   ⚠️  Supervisor routing failed: {exc}")

        # Fallback: keyword-based routing
        return self._fallback_routing(message)

    def _fallback_routing(self, message: str) -> RoutingDecision:
        """Keyword-based fallback when supervisor fails."""
        msg_lower = message.lower()

        agents = []
        if any(w in msg_lower for w in ["order", "package", "shipping", "track", "deliver", "cancel", "return", "wrong item"]):
            agents.append("order")
        if any(w in msg_lower for w in ["charge", "refund", "payment", "bill", "invoice", "price", "charged twice"]):
            agents.append("billing")
        if any(w in msg_lower for w in ["login", "password", "account", "email", "phone", "address", "app", "crash"]):
            agents.append("account")

        if not agents:
            agents = ["account"]  # default

        return RoutingDecision(
            target_agent=",".join(agents),
            reason="Fallback keyword routing",
            confidence=0.5,
            needs_human_review=False,
        )
