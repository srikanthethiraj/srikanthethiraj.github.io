---
layout: post
title: "Build a Multi-Agent Support System with Strands Agents and Amazon Bedrock"
tags: [AI, AWS, Python, Bedrock, Strands, Agents, AgentCore]
featured_image_thumbnail:
featured_image: assets/images/posts/2026/article-7-hero.jpeg
featured: false
hidden: false
---

In Part 6, we built a support assistant with guardrails, intent detection, and conversation history. It worked — but the routing was Python keyword matching. "Charge" goes to billing. "Password" goes to account. Simple, brittle, and wrong the moment a customer says "I got billed double" instead of "I was charged twice."

Your e-commerce company gets 200+ support tickets a day. Billing disputes, shipping problems, account issues — often multiple problems in the same message. "I was charged twice for my yoga mat AND I received the wrong color." That's two agents, not one. Keyword matching can't handle it.

This project replaces manual routing with agents that reason. A supervisor agent reads the customer's message, understands the intent, and delegates to specialized agents — each with their own tools and expertise. And it shows you three ways to build it: Bedrock Agents for prototyping, Strands for production code, and AgentCore for deployment at scale.

<!--more-->

## The Problem

A real support team doesn't have one person who handles everything. It has specialists — someone for billing, someone for shipping, someone for accounts. When a customer calls with multiple issues, the receptionist figures out who to involve and routes accordingly.

Part 6's assistant tried to be all three specialists at once. One system prompt, one set of tools, keyword-based routing. It couldn't handle "I was charged twice AND my package is late" because that's two specialists, not one.

You need a system where each specialist is an independent agent with its own tools, and a supervisor that understands natural language well enough to route correctly — even when the customer's message spans multiple domains.

## The Pattern

**Customer → Supervisor (reasons about routing) → Specialist Agent(s) → Tools → Response**

The supervisor doesn't use rules. It uses an LLM to read the message, understand the intent, and decide which agents to involve. The specialist agents don't share tools — each one has exactly the tools it needs for its domain.

## Three Ways to Build Agents on AWS

Before diving into the code, here's the landscape. AWS offers three approaches to building agents, and they're not alternatives — they're layers:

**Bedrock Agents (Managed Prototype)**
Configure an agent in the console or via API. AWS handles the orchestration loop, session memory, and scaling. Fast to set up, but you can't customize the reasoning, and each action group requires a Lambda function. Best for: quick prototypes and simple single-purpose agents.

**Strands Agents SDK (Code-First Build)**
Open-source Python SDK. You write the agent logic — tools as Python functions, system prompts, reasoning patterns. The agent decides which tools to use based on the prompt. Full control, local testing, fast iteration. Best for: custom agents, multi-agent systems, production code.

**Amazon Bedrock AgentCore (Production Deployment)**
Managed infrastructure for running agents at scale. Takes your Strands agent (or any framework), wraps it as an HTTP service, and handles compute, scaling, identity, memory, and observability. Best for: deploying agents to production without managing servers.

The progression: Prototype (Bedrock Agents) → Build (Strands) → Deploy (AgentCore).

## Architecture

The complete flow: customer message enters the supervisor, which routes to the right specialist agent(s). Each agent has its own tools. Responses go back to the customer. Sensitive actions (refunds over $50, angry customers) escalate to human review.

![Multi-Agent Support System](/assets/images/posts/2026/article-7-architecture.png)

## How the Supervisor Knows What to Do

This is the key question. The supervisor agent doesn't have routing rules or keyword matching. It has a system prompt that defines the available agents and their responsibilities:

```
ORDER AGENT — for: package tracking, shipping status, order cancellation, returns, wrong items
BILLING AGENT — for: payment questions, charges, refunds, duplicate charges, pricing
ACCOUNT AGENT — for: login issues, password resets, email/phone/address changes, app problems
```

Claude reads the customer's message, reasons about which categories the issue falls into, and returns a JSON routing decision:

```json
{
    "agents": ["billing", "order"],
    "reasoning": "Customer was charged twice (billing) AND received wrong item (order)",
    "priority": "high",
    "needs_human_review": true
}
```

The intelligence is in the reasoning. "I got billed double" routes to billing even though the word "charge" never appears. "My package vanished" routes to order even though "shipping" isn't mentioned. The LLM understands meaning, not keywords.

This is the fundamental difference from Article 6. Article 6: you write the routing rules. Article 7: the agent writes its own routing decisions.

## How It Works — The Agent Evolution

Each phase builds on the previous one's limitation.

### Phase 1: Bedrock Agents — The Quick Prototype

You can configure an order tracking agent in minutes using the Bedrock Agents API. Define the agent, add an action group with three actions (TrackOrder, LookupHistory, CancelOrder), and AWS handles the orchestration.

It works for simple, single-purpose agents. But you can't customize the reasoning loop, you can't test locally without deploying infrastructure, and adding a second agent type means creating a whole new managed agent.

When you need more control, that's where Strands comes in.

### Phase 2: Strands Agents — Full Code Control

Same order tracking agent, rebuilt with Strands. Tools are Python functions decorated with `@tool`. The agent decides which tools to call based on the customer's message.

```
Customer: Where is my order ORD-50435?
Agent: [calls track_order] → Your order is in transit with FedEx.
       Tracking: 794644790132. Estimated delivery: April 23rd.
```

The agent looked up the order, found the FedEx tracking number, and gave a specific answer with dates. No hardcoded responses — the tool returned real data and the agent formatted it naturally.

Single agents work great for focused tasks. But real customers have multi-part problems.

### Phase 3: Multi-Agent Orchestration

Three specialist agents, each with their own tools:

Order Agent — `track_order`, `lookup_order_history`, `cancel_order`
Billing Agent — `check_payment_status`, `process_refund`
Account Agent — `lookup_customer`, `reset_password`, `update_account_info`

A supervisor agent routes incoming requests. When a customer says "I was charged twice AND I received the wrong color," the supervisor delegates to both billing and order agents:

```
Supervisor: Routes to [billing, order] — "Two issues: duplicate charge + wrong item"

Billing Agent: Found duplicate charge of $167.76. Refund submitted
               for manager approval (over $50 threshold).

Order Agent: Confirmed wrong item flag on ORD-50398. Escalated to
             fulfillment team for correct color shipment.
```

Both agents worked independently on their part of the problem, using their own tools and domain knowledge.

### Phase 4: Human-in-the-Loop

Some actions are too risky for full automation. Refunds over $50 require manager approval. Angry customers get escalated to humans.

```
Customer: I need a full refund of $167.76.

Billing Agent: Refund submitted → PENDING APPROVAL (exceeds $50 threshold)
Supervisor: ⚠️ FLAGGED FOR HUMAN REVIEW
```

The agent doesn't just process the refund blindly. The `process_refund` tool has a built-in threshold — amounts over $50 return a "pending_approval" status. The supervisor also flags the ticket independently based on the refund amount and customer sentiment.

### Phase 5: AgentCore — Production Deployment

Everything works locally. But how do you run it in production with auto-scaling, identity, and observability?

AgentCore takes your Strands agent and deploys it as a managed service. The code change is minimal — wrap your agent function with `@app.entrypoint`:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()
agent = Agent(model=model, tools=[...], system_prompt="...")

@app.entrypoint
def invoke(payload):
    result = agent(payload["prompt"])
    return {"response": str(result)}
```

Test locally with `python agent_app.py` and `curl`. Deploy with `agentcore deploy --agent-name ecommerce-support`. AgentCore handles compute, scaling, IAM roles, session memory, and CloudWatch observability.

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

## When to Use What

| | Bedrock Agents | Strands Agents | AgentCore |
|---|---|---|---|
| **Best for** | Quick prototype | Custom build | Production deployment |
| **Control** | Low — AWS manages | Full — you own the code | Full — any framework |
| **Local testing** | Hard — needs infrastructure | Easy — runs locally | Easy — runs on port 8080 |
| **Multi-agent** | Separate managed agents | Native orchestration | Deploy any agent |
| **Cost** | Pay per invocation | Model costs only | Runtime + model costs |

The progression: Prototype with Bedrock Agents to validate the idea. Build with Strands when you need custom tools and multi-agent orchestration. Deploy with AgentCore when you're ready for production.

## What Changed from Part 6

| Concept | Part 6 (AI Support Assistant) | Part 7 (This Project) |
|---|---|---|
| **Routing** | Python keyword matching | LLM-based supervisor reasoning |
| **Agents** | One agent does everything | Three specialists + supervisor |
| **Tools** | Shared across all intents | Domain-specific per agent |
| **Multi-issue** | Can't handle | Supervisor delegates to multiple agents |
| **Framework** | Raw Bedrock Converse API | Strands Agents SDK |
| **Deployment** | Local only | AgentCore production-ready |

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

You'll see all 6 phases — Bedrock Agent concept, Strands single-agent, multi-agent routing, human-in-the-loop, and AgentCore deployment pattern.

Run all sample tickets end-to-end:

```bash
python run_all_tickets.py
```

Results are saved to `output/full_results.json` with every routing decision, agent response, and tool call.

## Tear Down

No infrastructure to tear down for the local demo. The AgentCore deployment files are in `agentcore-deploy/` — deploy when ready with:

```bash
pip install bedrock-agentcore-starter-toolkit
agentcore deploy --agent-name ecommerce-support
```

## What's Next

This is Part 7 of an ongoing series:

- **Part 1** — [Insurance Claim Processor](https://blog.srikanthethiraj.com/build-an-ai-powered-insurance-claim-processor-with-amazon-bedrock): Bedrock basics, prompt templates, simple RAG
- **Part 2** — [Financial Services AI Assistant](https://blog.srikanthethiraj.com/build-a-financial-services-ai-assistant-with-amazon-bedrock): benchmarking, circuit breakers, cross-region resilience
- **Part 3** — [Customer Feedback Pipeline](https://blog.srikanthethiraj.com/build-a-customer-feedback-pipeline-with-amazon-bedrock): multimodal data processing
- **Part 4** — RAG Knowledge Base: vector stores, embeddings, document chunking
- **Part 5** — Advanced Search & Retrieval: hybrid search, reranking, query expansion
- **Part 6** — AI Support Assistant with Governance: guardrails, prompt management, conversation flows
- **Part 7** — Multi-Agent Support System (this post): Strands Agents, Bedrock AgentCore, multi-agent orchestration
- **Part 8** — Multi-Tier Model Deployment & Enterprise Integration
- **Part 9** — AI Safety — Guardrails, PII Protection & Threat Detection
- **Part 10** — Cost & Latency Optimization for GenAI
- **Part 11** — AI Governance — Compliance, Fairness & Model Cards
- **Part 12** — Testing, Evaluation & Troubleshooting GenAI Systems

In Part 8, we take these agents and deploy them at enterprise scale — multi-tier model deployment, API Gateway integration, EventBridge event-driven processing, and model cascading based on query complexity.

Repository: [github.com/srikanthethiraj/agentic-ai-system](https://github.com/srikanthethiraj/agentic-ai-system)

---

*I'm Srikanth — a cloud engineer at AWS based in Austin, Texas. I learn by building, and I write about what I build. Follow along on this blog or connect with me on [LinkedIn](https://www.linkedin.com/in/srikanthethiraj/).*
