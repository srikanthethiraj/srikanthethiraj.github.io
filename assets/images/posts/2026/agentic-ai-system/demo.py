"""
Agentic AI System — Demo Script (Article 7)

Demonstrates building a multi-agent support system with Strands Agents:
  Phase 1: Single agent — tools as Python functions
  Phase 2: Multi-agent orchestration — supervisor + 3 specialists
  Phase 3: Human-in-the-loop — safety for sensitive actions

Deployment options (covered in Article 8) are shown as previews at the end.

Usage:
    python demo.py --region us-east-1
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.agents import create_order_agent, create_billing_agent, create_account_agent
from src.orchestrator import SupportOrchestrator
from src.bedrock_agent import demo_bedrock_inline_agent, demo_bedrock_agent_concept
from src.agentcore_deploy import demo_agentcore_concept, demo_harness_concept, write_agentcore_files


def main():
    parser = argparse.ArgumentParser(description="Agentic AI System demo")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--deploy", action="store_true",
                        help="Also show deployment options (Article 8 preview)")
    args = parser.parse_args()

    print("=" * 60)
    print("🤖 AGENTIC AI SYSTEM — E-COMMERCE SUPPORT DEMO")
    print("=" * 60)
    print(f"   Region: {args.region}")
    print(f"   Article 7: Build a Multi-Agent Support System")

    # ── Phase 1: Single Agent ──
    print(f"\n{'=' * 60}")
    print("📦 PHASE 1: Single Agent — Order Tracking")
    print(f"{'=' * 60}")

    order_agent = create_order_agent(args.region)
    query = "Customer CUST-1001 asks: Where is my order ORD-50435? When will it arrive?"
    print(f"\n   Customer: Where is my order ORD-50435?")
    print(f"   Agent working...")

    result = order_agent(query)
    print(f"\n   Order Agent: {str(result)[:500]}...")

    print(f"\n   ── Billing Agent ──")
    billing_agent = create_billing_agent(args.region)
    query = "Customer CUST-1003 asks: I think I was charged twice for order ORD-50398. Can you check?"
    print(f"\n   Customer: I think I was charged twice for order ORD-50398.")
    print(f"   Agent working...")

    result = billing_agent(query)
    print(f"\n   Billing Agent: {str(result)[:500]}...")

    print("\n   💡 Single agents work great for focused tasks. But real customers")
    print("   have multi-part problems. Next: multiple agents collaborating.")

    # ── Phase 2: Multi-Agent Orchestration ──
    print(f"\n{'=' * 60}")
    print("🔀 PHASE 2: Multi-Agent — Supervisor + Specialists")
    print(f"{'=' * 60}")

    orchestrator = SupportOrchestrator(region=args.region)

    message = "I was charged twice for my yoga mat order AND I received the wrong color. I want a refund and the correct item shipped."
    print(f"\n   Customer (CUST-1003): {message}")
    print(f"\n   Supervisor routing...")

    result = orchestrator.handle_request("CUST-1003", message)

    print(f"\n   Routing: {result['routing']}")
    for resp in result["responses"]:
        print(f"\n   [{resp['agent'].upper()} AGENT] ({resp['latency_ms']:.0f}ms):")
        print(f"   {resp['response'][:300]}...")

    print(f"\n   Total latency: {result['total_latency_ms']:.0f}ms")

    print("\n   💡 Multi-agent routing works. But some actions are too risky")
    print("   for full automation. Next: human approval for sensitive actions.")

    # ── Phase 3: Human-in-the-Loop ──
    print(f"\n{'=' * 60}")
    print("👤 PHASE 3: Human-in-the-Loop — Refund Approval")
    print(f"{'=' * 60}")

    message = "I need a full refund of $167.76 for order ORD-50398. The yoga mat was the wrong color and I've been charged twice."
    print(f"\n   Customer (CUST-1003): {message}")

    result = orchestrator.handle_request("CUST-1003", message)

    for resp in result["responses"]:
        print(f"\n   [{resp['agent'].upper()} AGENT] ({resp['latency_ms']:.0f}ms):")
        print(f"   {resp['response'][:400]}...")

    if result["routing"]["needs_human_review"]:
        print(f"\n   ⚠️  FLAGGED FOR HUMAN REVIEW")
        print(f"   Reason: Refund amount exceeds $50 threshold")

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print("✅ Article 7 demo complete — Multi-Agent System Built")
    print(f"{'=' * 60}")
    print()
    print("   What we built:")
    print("   Phase 1: Single agent with @tool functions")
    print("   Phase 2: Supervisor + 3 specialists collaborating")
    print("   Phase 3: Human-in-the-loop safety for sensitive actions")
    print()
    print("   Next: Article 8 covers three ways to deploy this system.")
    print("   Run with --deploy flag to preview deployment options.")

    # ── Deployment Preview (Article 8) ──
    if args.deploy:
        print(f"\n{'=' * 60}")
        print("🚀 DEPLOYMENT PREVIEW (Article 8)")
        print(f"{'=' * 60}")

        print(f"\n{'─' * 60}")
        print("   OPTION 1: Bedrock Agents — Fully Managed")
        print(f"{'─' * 60}")
        result = demo_bedrock_inline_agent(args.region)
        if "error" in result:
            demo_bedrock_agent_concept()

        print(f"\n{'─' * 60}")
        print("   OPTION 2: AgentCore Harness — Config-Only (Preview)")
        print(f"{'─' * 60}")
        demo_harness_concept()

        print(f"\n{'─' * 60}")
        print("   OPTION 3: AgentCore + Custom Code — Full Control")
        print(f"{'─' * 60}")
        demo_agentcore_concept()

        deploy_dir = os.path.join(os.path.dirname(__file__), "agentcore-deploy")
        paths = write_agentcore_files(deploy_dir)
        print(f"\n   Deployment files written to {deploy_dir}/:")
        for filename in paths:
            print(f"     - {filename}")


if __name__ == "__main__":
    main()
