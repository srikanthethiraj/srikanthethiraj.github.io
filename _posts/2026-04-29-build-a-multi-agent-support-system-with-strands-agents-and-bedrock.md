---
layout: post
title: "Build a Multi-Agent Support System with Strands Agents and Amazon Bedrock"
tags: [AI, AWS, Python, Bedrock, Strands, Agents]
featured_image_thumbnail:
featured_image: assets/images/posts/2026/article-7-hero.jpeg
featured: false
hidden: false
---

In Part 6, we built a support assistant with guardrails, intent detection, and conversation history. It worked — but the routing was Python keyword matching. "Charge" goes to billing. "Password" goes to account. Simple, brittle, and wrong the moment a customer says "I got billed double" instead of "I was charged twice."

Your e-commerce company gets 200+ support tickets a day. Billing disputes, shipping problems, account issues — often multiple problems in the same message. "I was charged twice for my yoga mat AND I received the wrong color." That's two agents, not one. Keyword matching can't handle it.

This project replaces manual routing with agents that reason. A supervisor agent reads the customer's message, understands the intent, and delegates to specialized agents — each with their own tools and expertise. We build it with the Strands Agents SDK — an open-source Python framework where tools are just decorated functions.

<!--more-->

## The Problem

A real support team doesn't have one person who handles everything. It has specialists — someone for billing, someone for shipping, someone for accounts. When a customer calls with multiple issues, the receptionist figures out who to involve and routes accordingly.

Part 6's assistant tried to be all three specialists at once. One system prompt, one set of tools, keyword-based routing. It couldn't handle "I was charged twice AND my package is late" because that's two specialists, not one.

You need a system where each specialist is an independent agent with its own tools, and a supervisor that understands natural language well enough to route correctly — even when the customer's message spans multiple domains.

## The Pattern

**Customer → Supervisor (reasons about routing) → Specialist Agent(s) → Tools → Response**

The supervisor doesn't use rules. It uses an LLM to read the message, understand the intent, and decide which agents to involve. The specialist agents don't share tools — each one has exactly the tools it needs for its domain.

## How It Works — Three Phases

Each phase builds on the previous one's limitation.

### Phase 1: Build a Single Agent with Strands

Strands is an open-source Python SDK where tools are just decorated functions. The agent runs in your process, calls tools directly, and you control every step.

**Step 1: Define tools as Python functions.**
A `@tool` decorator turns any function into something the agent can call. The function's docstring tells the agent what it does — and the function body is the actual execution logic.

```python
@tool
def track_order(order_id: str) -> dict:
    """Track the shipping status of an order."""
    order = ORDERS.get(order_id)
    return {
        "order_id": order_id,
        "status": order["status"],
        "carrier": order["shipping_carrier"],
        "tracking_number": order["tracking_number"],
        "estimated_delivery": order["estimated_delivery"],
    }
```

This is a plain Python function. It works locally, it's easy to test with mocks, and — as we'll see in Part 8 — the same function can be deployed as a Lambda handler or inside an AgentCore container without rewriting it.

**Step 2: Create the agent with a system prompt and tools.**
One `Agent()` call wires everything together — the model, the persona, and the list of tool functions.

```python
from strands import Agent
from strands.models import BedrockModel

agent = Agent(
    model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0"),
    system_prompt="You are an order support agent. Use tools to look up real data.",
    tools=[track_order, lookup_order_history, cancel_order],
)
```

**Step 3: The agent handles the entire conversation in one call.**
You pass the customer's message. The agent reasons about it, decides which tool to call, executes the function directly in your Python process, reads the result, and writes the response — all in a single call.

```python
result = agent("Customer CUST-1001 asks: Where is my order ORD-50435?")
```

Here's what happens behind the scenes. The agent repeats a decision cycle: read the message → decide if a tool is needed → call the tool → read the result → decide if more tools are needed → respond. This cycle runs entirely in your Python process — no API round-trips for tool execution.

```
Agent reasoning:
  → Reads query: customer wants order tracking
  → Picks tool: track_order(order_id="ORD-50435")
  → Calls the Python function directly — gets result instantly
  → Formats response from the data

Agent: Your order ORD-50435 is currently in transit with FedEx.
       Tracking number: 794644790132. Estimated delivery: April 23rd.
```

If the agent needs two tools (track the order AND check payment), it calls both in sequence automatically — one `agent()` call, no extra round-trips.

**What single agents do well:**
- Full control over the decision cycle — add custom logic between tool calls
- Tools are Python functions — test with mocks, run offline, iterate fast
- Open-source — inspect, extend, contribute

**The limitation:**
Single agents can't handle "I was charged twice AND my package is late." That's two domains, two tool sets. One agent trying to do everything gives worse answers than focused specialists. You need multiple agents collaborating.

### Phase 2: Multi-Agent Orchestration — The Supervisor Pattern

**Step 1: Define three specialist agents, each with their own tools.**
Each agent has a focused system prompt and only the tools it needs. The order agent can't process refunds. The billing agent can't track packages. This separation means each agent is an expert in its domain.

```python
order_agent = Agent(
    model=model,
    system_prompt="You are the Order Support Agent...",
    tools=[track_order, lookup_order_history, cancel_order],
)
billing_agent = Agent(
    model=model,
    system_prompt="You are the Billing Support Agent...",
    tools=[check_payment_status, process_refund],
)
account_agent = Agent(
    model=model,
    system_prompt="You are the Account Support Agent...",
    tools=[lookup_customer, reset_password, update_account_info],
)
```

**Step 2: Create a supervisor agent that routes requests.**
The supervisor doesn't have domain tools. It has one job: read the customer's message, figure out which specialists to involve, and return a routing decision as JSON.

```python
supervisor = Agent(
    model=model,
    system_prompt="""Analyze the customer's message and route to specialists:
    ORDER AGENT — for: tracking, shipping, cancellations, returns, wrong items
    BILLING AGENT — for: payments, charges, refunds, duplicate charges
    ACCOUNT AGENT — for: login, password, email/phone changes, app issues

    Return JSON: {"agents": [...], "reasoning": "...", "needs_human_review": true/false}""",
    tools=[lookup_customer],
)
```

How does the supervisor know what to do? It reads the customer's message and matches it against the agent descriptions in its system prompt. "I got billed double" → the word "billed" matches the billing agent's description. "My package vanished" → "package" matches the order agent. The LLM understands meaning, not keywords — that's the fundamental difference from Article 6's Python keyword matching.

**Step 3: The orchestrator ties it all together.**
When a customer message arrives, the orchestrator sends it to the supervisor first. The supervisor returns which agents to involve. The orchestrator dispatches to each specialist in sequence, collects their responses, and checks for human review flags.

```python
# Supervisor analyzes: "I was charged twice AND received the wrong color"
routing = supervisor(message)  # → {"agents": ["billing", "order"], ...}

# Dispatch to each specialist
for agent_name in routing["agents"]:
    response = agents[agent_name](message)  # Each agent uses its own tools
```

```
Supervisor: Routes to [billing, order] — "Two issues: duplicate charge + wrong item"

Billing Agent: Found duplicate charge of $167.76. Refund submitted
               for manager approval (over $50 threshold).

Order Agent: Confirmed wrong item flag on ORD-50398. Escalated to
             fulfillment team for correct color shipment.
```

Both agents worked independently on their part of the problem, using their own tools and domain knowledge.

**What multi-agent orchestration does well:**
- Handles complex, multi-issue requests that single agents can't
- Each specialist is focused — better answers than one agent trying to do everything
- Supervisor reasoning is transparent — you can audit why each agent was chosen
- Agents are independent — add a new specialist without changing existing ones

**The limitation:**
The agents can do anything their tools allow — including processing a $500 refund without asking anyone. Some actions need human approval.

### Phase 3: Human-in-the-Loop — Safety for Sensitive Actions

**Step 1: Tools enforce business rules.**
The `process_refund` tool has a built-in threshold. Amounts over $50 return a "pending_approval" status instead of processing immediately. The tool doesn't need the agent's permission — it's a hard business rule in the code.

```python
@tool
def process_refund(customer_id: str, order_id: str, amount: float, reason: str) -> dict:
    """Process a refund. Amounts over $50 require manager approval."""
    if amount > 50:
        return {
            "status": "pending_approval",
            "message": f"Refund of ${amount:.2f} requires manager approval (threshold: $50).",
            "approval_required": True,
        }
    return {"status": "approved", "amount": amount, ...}
```

**Step 2: The supervisor independently flags tickets for human review.**
The supervisor's routing decision includes a `needs_human_review` field. It flags based on refund amounts, customer sentiment, and escalation phrases — independent of what the tools do. Two layers of safety: the tool blocks the action, and the supervisor flags the ticket.

**Step 3: The orchestrator checks both layers.**
After all agents respond, the orchestrator checks the supervisor's flag AND scans agent responses for pending approvals. If either triggers, the ticket is marked for human review.

```
Customer: I need a full refund of $167.76.

Billing Agent: Refund submitted → PENDING APPROVAL (exceeds $50 threshold)
Supervisor: ⚠️ FLAGGED FOR HUMAN REVIEW
```

The customer gets a response explaining the refund is pending approval. The human agent gets a ticket with the full context — customer history, agent reasoning, and the specific action that needs approval.

**What human-in-the-loop does well:**
- Two independent safety layers — tool-level rules AND supervisor-level flags
- Business rules are in code, not prompts — the $50 threshold can't be prompt-injected away
- Human agents get full context — they don't start from scratch
- Configurable thresholds — change the dollar amount without retraining anything

## Real Results — 8 Tickets End-to-End

We ran all 8 sample tickets through the full system — supervisor routing, sub-agent execution, tool calls, and response generation:

```
Ticket     Agents              Review    Latency
TKT-001    order                   No    10601ms
TKT-002    billing            ⚠️ YES    10902ms
TKT-003    account                 No    12471ms
TKT-004    billing,order      ⚠️ YES    22593ms
TKT-005    billing,order      ⚠️ YES    23603ms
TKT-006    order                   No    10633ms
TKT-007    account                 No    12405ms
TKT-008    account                 No    14047ms
```

Every ticket routed correctly. Multi-issue tickets (TKT-004, TKT-005) went to multiple agents. Money-related issues got flagged for human review. The supervisor considered customer loyalty tier — Platinum customers with billing issues got higher priority.

## What Changed from Part 6

| Concept | Part 6 (AI Support Assistant) | Part 7 (This Project) |
|---|---|---|
| **Routing** | Python keyword matching | LLM-based supervisor reasoning |
| **Agents** | One agent does everything | Three specialists + supervisor |
| **Tools** | Shared across all intents | Domain-specific per agent |
| **Multi-issue** | Can't handle | Supervisor delegates to multiple agents |
| **Framework** | Raw Bedrock Converse API | Strands Agents SDK |

## Getting Started

Prerequisites: Python 3.10+, AWS CLI configured, Bedrock model access for Claude Sonnet 4.

```bash
git clone https://github.com/srikanthethiraj/agentic-ai-system.git
cd agentic-ai-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the demo:

```bash
python demo.py --region us-east-1
```

Run all sample tickets end-to-end:

```bash
python run_all_tickets.py
```

Results are saved to `output/full_results.json` with every routing decision, agent response, and tool call.

## Tear Down

No infrastructure to tear down — the demo runs locally against Bedrock APIs.

## What's Next

The multi-agent system works on your machine. But how do you take it to production? In Part 8, we deploy the same system three ways on AWS — Bedrock Agents (fully managed), AgentCore Harness (config-only), and AgentCore with custom code (full control). Same tools, same logic, three deployment paths.

This is Part 7 of an ongoing series:

- **Part 1** — [Insurance Claim Processor](https://blog.srikanthethiraj.com/build-an-ai-powered-insurance-claim-processor-with-amazon-bedrock): Bedrock basics, prompt templates, simple RAG
- **Part 2** — [Financial Services AI Assistant](https://blog.srikanthethiraj.com/build-a-financial-services-ai-assistant-with-amazon-bedrock): benchmarking, circuit breakers, cross-region resilience
- **Part 3** — [Customer Feedback Pipeline](https://blog.srikanthethiraj.com/build-a-customer-feedback-pipeline-with-amazon-bedrock): multimodal data processing
- **Part 4** — [RAG Knowledge Base](https://blog.srikanthethiraj.com/build-a-rag-knowledge-base-with-amazon-bedrock-and-opensearch): vector stores, embeddings, document chunking
- **Part 5** — [Advanced Search & Retrieval](https://blog.srikanthethiraj.com/optimize-rag-search-with-hybrid-retrieval-and-reranking-on-aws): hybrid search, reranking, query expansion
- **Part 6** — [AI Support Assistant with Governance](https://blog.srikanthethiraj.com/build-an-ai-support-assistant-with-bedrock-guardrails-and-governance): guardrails, prompt management, conversation flows
- **Part 7** — Multi-Agent Support System (this post): Strands Agents, multi-agent orchestration
- **Part 8** — Deploy AI Agents on AWS: Bedrock Agents vs AgentCore
- **Part 9** — Multi-Tier Model Deployment & Enterprise Integration
- **Part 10** — AI Safety — Guardrails, PII Protection & Threat Detection
- **Part 11** — Cost & Latency Optimization for GenAI
- **Part 12** — AI Governance — Compliance, Fairness & Model Cards
- **Part 13** — Testing, Evaluation & Troubleshooting GenAI Systems

Repository: [github.com/srikanthethiraj/agentic-ai-system](https://github.com/srikanthethiraj/agentic-ai-system)

---

*I'm Srikanth — a cloud engineer at AWS based in Austin, Texas. I learn by building, and I write about what I build. Follow along on this blog or connect with me on [LinkedIn](https://www.linkedin.com/in/srikanthethiraj/).*
