# Multi-Agent Support System — Strands Agents & Amazon Bedrock

Build a multi-agent e-commerce customer support system with Strands Agents. A supervisor agent reasons about customer requests and delegates to specialized agents — each with their own tools and expertise.

This is **Part 7** of a hands-on series on building AI applications with AWS. Part 8 covers deploying this system three ways on AWS.

## Hey, I'm Srikanth 👋

I'm a cloud engineer at AWS based in Austin, Texas. In Part 6, we built a support assistant with guardrails and intent detection. It worked — but the routing was Python keyword matching. "Charge" goes to billing. "Password" goes to account. Brittle, and wrong the moment a customer says "I got billed double."

This project replaces manual routing with agents that reason. You'll build the system in three phases with Strands Agents — single agent, multi-agent orchestration, and human-in-the-loop safety.

Let's build it.

> Follow along on my blog: [blog.srikanthethiraj.com](https://blog.srikanthethiraj.com/)
> Connect with me: [LinkedIn](https://www.linkedin.com/in/srikanthethiraj/)

---

## Why This Matters — Before vs After

| | Part 6 (AI Support Assistant) | Part 7 (This Project) |
|---|---|---|
| **Routing** | Python keyword matching | LLM-based supervisor reasoning |
| **Agents** | One agent does everything | Three specialists + supervisor |
| **Tools** | Shared across all intents | Domain-specific per agent |
| **Multi-issue** | Can't handle | Supervisor delegates to multiple agents |
| **Framework** | Raw Bedrock Converse API | Strands Agents SDK |

### The Pattern

> **Customer → Supervisor (reasons) → Specialist Agent(s) → Tools → Response**

## What You'll Learn

- Tools as Python functions with the `@tool` decorator
- Multi-agent orchestration with a supervisor routing pattern
- How the supervisor knows what to do (system prompt → LLM reasoning)
- Human-in-the-loop approval workflows for sensitive actions
- Two independent safety layers: tool-level rules + supervisor-level flags

## Architecture

```
❓ Customer Message
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                Multi-Agent Support System                  │
│                                                            │
│  Supervisor Agent (Claude) ──── reasons about routing      │
│       │         │         │                                │
│       ▼         ▼         ▼                                │
│  Order Agent  Billing   Account                            │
│  track_order  Agent     Agent                              │
│  cancel_order check_pay reset_pw                           │
│  order_hist   refund    update_info                        │
│       │         │                                          │
│       ▼         ▼                                          │
│  Human Review (refunds > $50, angry customers)             │
└──────────────────────────────────────────────────────────┘
```

## How It Works — Three Phases

Each phase builds on the previous one's limitation.

### Phase 1: Single Agent — Full Code Control

Tools as Python functions, local testing, fast iteration.

**What you get:** Custom tools with `@tool`, full control over the agent's decision cycle, local testing with mocks.
**The wall:** A single agent can't handle multi-part customer problems.

### Phase 2: Multi-Agent Orchestration

Three specialist agents + supervisor. Customer says "charged twice AND wrong item" → both billing and order agents collaborate.

**What you get:** Autonomous routing to the right specialist(s), handles multi-issue requests.
**The wall:** Some actions are too risky for full automation.

### Phase 3: Human-in-the-Loop

Refunds over $50 require manager approval. Angry customers get escalated. Two safety layers: tool-level rules AND supervisor-level flags.

**What you get:** Safety guardrails on autonomous actions with full context for human reviewers.

## Example Output — 8 Tickets End-to-End

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

Every ticket routed correctly. Multi-issue tickets went to multiple agents. Money issues flagged for human review.

---

## Prerequisites

1. **Python 3.10+** installed
2. **AWS CLI** configured with credentials
3. **Bedrock model access** for Claude Sonnet 4

---

## Step-by-Step Setup Guide

### Step 1: Clone and Install

```bash
git clone https://github.com/srikanthethiraj/agentic-ai-system.git
cd agentic-ai-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Run the Demo

```bash
python demo.py --region us-east-1
```

Three phases: single agent → multi-agent routing → human-in-the-loop.

To also preview deployment options (covered in Article 8):

```bash
python demo.py --region us-east-1 --deploy
```

### Step 3: Run All Tickets

```bash
python run_all_tickets.py
```

Results saved to `output/full_results.json`.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ValidationException` on Bedrock | Use inference profile IDs (e.g., `us.anthropic.claude-sonnet-4-20250514-v1:0`) |
| `AccessDeniedException` | Enable Claude Sonnet 4 in Bedrock console |
| `ModuleNotFoundError: strands` | `pip install strands-agents strands-agents-tools` |
| Supervisor returns invalid JSON | Fallback keyword routing kicks in automatically |

## Tear Down

No infrastructure to tear down — the demo runs locally against Bedrock APIs.

## Project Structure

```
agentic-ai-system/
├── demo.py                    # Article 7 demo (build phases + optional deploy preview)
├── run_all_tickets.py         # Run all sample tickets end-to-end
├── requirements.txt
├── README.md
├── agentcore-deploy/          # AgentCore deployment files (Article 8)
│   ├── agent_app.py           # @app.entrypoint wrapper
│   ├── Dockerfile
│   └── requirements.txt
├── samples/
│   └── sample_tickets.json    # 8 customer support tickets (pure input)
├── src/
│   ├── __init__.py
│   ├── models.py              # Data models
│   ├── sample_data.py         # E-commerce backend (customers, orders, payments)
│   ├── tools.py               # @tool functions (track_order, process_refund, etc.)
│   ├── agents.py              # Specialist agents + supervisor
│   ├── orchestrator.py        # Multi-agent orchestrator
│   ├── bedrock_agent.py       # Bedrock Agents deployment (Article 8)
│   ├── agentcore_deploy.py    # AgentCore deployment generator (Article 8)
│   └── evaluator.py           # Run tickets and show agent decisions
├── output/
│   ├── routing_decisions.json
│   └── full_results.json
└── tests/
```

## Connection to Part 6

| Concept | Part 6 | Part 7 |
|---|---|---|
| **Routing** | Keyword matching | LLM supervisor reasoning |
| **Agents** | One agent | Three specialists + supervisor |
| **Tools** | Shared | Domain-specific per agent |
| **Multi-issue** | Can't handle | Routes to multiple agents |
| **Framework** | boto3 Converse API | Strands Agents SDK |

## What's Next in the Series

This is Part 7 of an ongoing series:

| Part | Project | What You'll Build |
|---|---|---|
| **1** | **[Insurance Claim Processor](https://blog.srikanthethiraj.com/build-an-ai-powered-insurance-claim-processor-with-amazon-bedrock)** | AI-powered document extraction |
| **2** | **[Financial Services AI Assistant](https://blog.srikanthethiraj.com/build-a-financial-services-ai-assistant-with-amazon-bedrock)** | Benchmarking, circuit breakers |
| **3** | **[Customer Feedback Pipeline](https://blog.srikanthethiraj.com/build-a-customer-feedback-pipeline-with-amazon-bedrock)** | Multimodal data processing |
| **4** | **[RAG Knowledge Base](https://blog.srikanthethiraj.com/build-a-rag-knowledge-base-with-amazon-bedrock-and-opensearch)** | Vector stores, embeddings |
| **5** | **[Advanced Search & Retrieval](https://blog.srikanthethiraj.com/optimize-rag-search-with-hybrid-retrieval-and-reranking-on-aws)** | Hybrid search, reranking |
| **6** | **[AI Support Assistant](https://blog.srikanthethiraj.com/build-an-ai-support-assistant-with-bedrock-guardrails-and-governance)** | Guardrails, prompt management |
| **7** | **Multi-Agent Support System** (this project) | Strands Agents, multi-agent orchestration |
| **8** | **Deploy AI Agents on AWS** | Bedrock Agents vs AgentCore |
| **9+** | **Coming soon** | Enterprise integration, safety, optimization, governance, testing |

## License

MIT
