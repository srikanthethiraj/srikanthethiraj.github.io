"""Run all sample tickets through the full end-to-end workflow.

Supervisor routes → Sub-agents execute → Tools called → Results saved.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.orchestrator import SupportOrchestrator
from src.evaluator import load_sample_tickets


def main():
    region = "us-east-2"
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("🎫 RUNNING ALL 8 TICKETS — FULL END-TO-END")
    print("=" * 60)

    orchestrator = SupportOrchestrator(region=region)
    tickets = load_sample_tickets(os.path.join(os.path.dirname(__file__), "samples"))

    all_results = []

    for ticket in tickets:
        tid = ticket["ticket_id"]
        cid = ticket["customer_id"]
        msg = ticket["message"]

        print(f"\n{'─' * 60}")
        print(f"🎫 {tid} | {cid}")
        print(f"   \"{msg[:80]}{'...' if len(msg) > 80 else ''}\"")
        print(f"{'─' * 60}")

        result = orchestrator.handle_request(cid, msg)

        # Summarize
        agents = result["routing"]["agents"]
        human = result["routing"]["needs_human_review"]
        latency = result["total_latency_ms"]

        print(f"\n   Summary:")
        print(f"   Agents: {', '.join(agents)}")
        print(f"   Human review: {'YES' if human else 'No'}")
        print(f"   Latency: {latency:.0f}ms")

        all_results.append({
            "ticket_id": tid,
            "customer_id": cid,
            "message": msg,
            "routing": result["routing"],
            "responses": [
                {
                    "agent": r["agent"],
                    "response": r["response"],
                    "latency_ms": r["latency_ms"],
                }
                for r in result["responses"]
            ],
            "total_latency_ms": latency,
        })

    # Save all results
    output_path = os.path.join(output_dir, "full_results.json")
    with open(output_path, "w") as f:
        json.dump({"tickets_processed": len(all_results), "results": all_results}, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"✅ All {len(all_results)} tickets processed.")
    print(f"   Results saved to {output_path}")

    # Summary table
    print(f"\n   {'Ticket':<10} {'Agents':<20} {'Review':>8} {'Latency':>10}")
    print(f"   {'─' * 10} {'─' * 20} {'─' * 8} {'─' * 10}")
    for r in all_results:
        agents = ",".join(r["routing"]["agents"])
        review = "⚠️ YES" if r["routing"]["needs_human_review"] else "No"
        print(f"   {r['ticket_id']:<10} {agents:<20} {review:>8} {r['total_latency_ms']:>8.0f}ms")


if __name__ == "__main__":
    main()
