"""Run sample tickets through the system and show agent decisions.

The point: the reader sees the supervisor and agents making autonomous
decisions — routing, tool selection, human review flags — all from
just a customer message. No pre-configured rules, no lookup tables.
"""

from __future__ import annotations

import json
import os

from .orchestrator import SupportOrchestrator


def load_sample_tickets(samples_dir: str = None) -> list[dict]:
    """Load sample tickets from JSON."""
    if not samples_dir:
        samples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")
    path = os.path.join(samples_dir, "sample_tickets.json")
    with open(path) as f:
        return json.load(f)


def run_ticket_batch(orchestrator: SupportOrchestrator, tickets: list[dict], output_dir: str = None) -> list[dict]:
    """Run a batch of tickets and capture what the agents decided.

    For each ticket, shows:
    - Which agent(s) the supervisor chose
    - Why it made that choice
    - Whether it flagged for human review

    Saves results to output/routing_decisions.json if output_dir is provided.
    """
    results = []

    for ticket in tickets:
        customer_id = ticket["customer_id"]
        message = ticket["message"]

        # Get the routing decision (just routing, not full execution)
        routing = orchestrator._route_request(customer_id, message)

        results.append({
            "ticket_id": ticket["ticket_id"],
            "customer_id": customer_id,
            "message": message,
            "agents_chosen": sorted(a.strip() for a in routing.target_agent.split(",")),
            "reasoning": routing.reason,
            "confidence": routing.confidence,
            "human_review": routing.needs_human_review,
        })

    # Save to output file
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "routing_decisions.json")
        with open(output_path, "w") as f:
            json.dump({"decisions": results, "total_tickets": len(results)}, f, indent=2)
        print(f"\n   Saved routing decisions to {output_path}")

    return results


def print_routing_decisions(results: list[dict]) -> None:
    """Print what the supervisor decided for each ticket."""
    print(f"\n   {'Ticket':<10} {'Agent(s) Chosen':<20} {'Human Review':>14}")
    print(f"   {'─' * 10} {'─' * 20} {'─' * 14}")

    for r in results:
        agents = ",".join(r["agents_chosen"])
        review = "⚠️  YES" if r["human_review"] else "No"
        print(f"   {r['ticket_id']:<10} {agents:<20} {review:>14}")

    print(f"\n   The supervisor made these decisions autonomously —")
    print(f"   no routing rules, no keyword matching, just reasoning.")
