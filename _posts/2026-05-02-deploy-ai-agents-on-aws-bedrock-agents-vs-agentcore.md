---
layout: post
title: "Deploy AI Agents on AWS — Bedrock Agents vs AgentCore"
tags: [AI, AWS, Python, Bedrock, Agents, AgentCore, Strands]
featured_image_thumbnail:
featured_image: assets/images/posts/2026/article-8-hero.jpeg
featured: false
hidden: false
---

In Part 7, we built a multi-agent support system with Strands Agents — a supervisor that routes customer requests to three specialist agents, with human-in-the-loop safety for sensitive actions. It works on your machine. Now how do you run it in production?

Here's a story I keep hearing: teams ship on Bedrock Agents, love the speed — declare an agent, AWS runs it, done in minutes. Then they need a second agent. Then custom routing. Then human-in-the-loop. And they hit a ceiling.

The good news: AWS has an answer for every stage of that journey. And the same Python tools work across all of them — you write the business logic once, the deployment wrapper changes.

<!--more-->

## One Codebase, Three Deployment Paths

The tools you built in Part 7 (`track_order`, `process_refund`, `reset_password`) are plain Python functions. They work everywhere:

| Deployment | How tools run | What changes |
|---|---|---|
| **Local (Strands)** | Direct function calls in your process | Nothing — this is where you built them |
| **Bedrock Agents** | Lambda handler wraps the same functions | Add `lambda_handler` wrapper |
| **AgentCore Harness** | Tools connect via AgentCore Gateway/MCP | Declare tools in harness config |
| **AgentCore + Custom** | Same Strands code in a container | Add `@app.entrypoint` wrapper |

You write the business logic once. The deployment wrapper changes, not the tools.

---

## Option 1: Bedrock Agents — The On-Ramp

Bedrock Agents solved the first-agent problem. Declare an agent in the console or via API, attach Lambda functions for tools, and AWS handles the reasoning loop, tool execution, session memory, and scaling. Built-in Knowledge Bases for RAG, Guardrails for safety, console UI for non-developers. Zero orchestration code.

**How your tools become Lambda functions:**

```python
def lambda_handler(event, context):
    function_name = event["function"]
    parameters = {p["name"]: p["value"] for p in event["parameters"]}

    if function_name == "TrackOrder":
        result = track_order(parameters["order_id"])  # Same function from Part 7!
        return {"response": json.dumps(result)}
```

**How you deploy multi-agent:** Bedrock Agents supports supervisor/collaborator patterns natively. Create each specialist as a separate agent with its own Lambda tools, then associate them with a supervisor using `associate_agent_collaborator`. The supervisor routes automatically based on natural language instructions — one API call, AWS handles delegation and response combination.

**What Bedrock Agents does well:**
- Zero orchestration code — configure, don't build
- Multi-agent collaboration built in
- Built-in Knowledge Bases, Guardrails, and session memory
- Console-first — non-developers can create and test agents
- Production scaling and CloudWatch observability out of the box

**The ceiling (structural, not cosmetic):**
- No prompt caching — every turn pays full input token cost (managed loop doesn't use Converse API)
- No extended thinking, no multimodal input (`inputText` only)
- Tools run sequentially — no parallel calling
- Can't add code-level routing logic (e.g., "if Platinum customer, prioritize billing")
- No single artifact to run locally — logic spread across IAM, Lambda, OpenAPI, Bedrock config
- Changing model or tools requires prepare-and-redeploy

What if you want the declarative experience back — but without these limitations? That's the harness.

---

## Option 2: AgentCore Harness — Declarative Without the Ceiling

The [managed harness](https://aws.amazon.com/blogs/machine-learning/get-to-your-first-working-agent-in-minutes-announcing-new-features-in-amazon-bedrock-agentcore/) brings back the "declare and deploy" experience, but on the AgentCore platform. Three API calls. No Lambda, no Dockerfile, no orchestration code. Powered by Strands under the hood.

> Currently in preview: US West (Oregon), US East (N. Virginia), Asia Pacific (Sydney), Europe (Frankfurt).

```python
agentcore.create_agent(
    name="order-support",
    model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    instructions="You are an order support agent. Help customers track packages.",
    tools=[track_order, lookup_order_history],
)

response = agentcore.invoke_agent(
    agent_name="order-support",
    prompt="Where is my order ORD-50435?",
)
```

**The key differentiator from Bedrock Agents: per-invocation overrides.** Change the model, tools, or system prompt on any single call without redeploying:

```bash
# Swap model for one call — no redeployment
agentcore invoke --agent-name order-support \
  --model-id anthropic.claude-3-5-haiku-20241022-v1:0 \
  --prompt "Where is my order?"
```

Tools connect via AgentCore Gateway using MCP. If you have existing Lambda functions from Bedrock Agents, wrap them behind a Gateway — the harness consumes them without rewriting Lambda code. Your investment carries forward.

**What the harness does well:**
- Three API calls to production — fastest deploy path
- Per-invocation overrides — swap model, tools, prompt per call
- Multi-model — Bedrock, OpenAI, Gemini, switch mid-session
- Built-in code interpreter and shell access
- MCP tool discovery via Gateway — reuse existing Lambdas
- Custom container images for non-standard environments

**The ceiling:**
- **Single agent only** — no multi-agent routing, no supervisor/collaborator
- No built-in Knowledge Bases or Guardrails (connect via Gateway/MCP)
- Custom orchestration loops (tree-of-thought, A2A handoffs) need Runtime
- In preview — 4 regions, API may change

The harness is the fastest path for single agents. But our Part 7 system has a supervisor routing to three specialists with human-in-the-loop safety. That's custom orchestration — config alone can't express it.

---

## Option 3: AgentCore + Custom Code — Full Control

This is where our Part 7 system ends up. The supervisor, three specialist agents, and human-in-the-loop routing — deployed on managed infrastructure with the same code we tested locally.

**Why not Bedrock Agents (Option 1)?** Both do multi-agent. The difference:

| | Bedrock Agents | AgentCore + Custom |
|---|---|---|
| **Routing logic** | Natural language instructions | Your Python code — any logic |
| **Human-in-the-loop** | Not built-in | Your code (tool thresholds + flags) |
| **Local testing** | Needs deployed agents | `python agent_app.py` + curl |
| **Prompt caching** | Not available | Available (direct API) |
| **Framework** | Bedrock Agents only | Strands, LangGraph, CrewAI, anything |

**How it works:**

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from orchestrator import SupportOrchestrator

app = BedrockAgentCoreApp()
orchestrator = SupportOrchestrator()

@app.entrypoint
def invoke(payload):
    result = orchestrator.handle_request(
        customer_id=payload["customer_id"],
        message=payload["prompt"],
    )
    return result
```

Test locally, deploy with one command:

```bash
python agent_app.py  # Test on port 8080
agentcore deploy --agent-name ecommerce-support  # Deploy to production
```

Migrating from Bedrock Agents? The CLI scaffolds the project:
```bash
agentcore import-agent --agent-id YOUR_AGENT_ID --target-platform strands
```

**What AgentCore adds on top of your code:**
- Auto-scaling, microVM isolation per session, persistent filesystem
- IAM roles per agent, CloudWatch traces/metrics/logs
- Agents can suspend mid-task and resume (human approval workflows)
- Every Bedrock feature — prompt caching (up to 90% savings), extended thinking, multimodal

**The tradeoff:**
- You write the orchestration code and deployment wrapper
- No built-in KB, Guardrails, or console UI
- Runtime compute cost on top of model costs

---

## How to Decide

**"I don't want to write orchestration code."**
→ **Bedrock Agents**. Managed single + multi-agent, built-in KB/Guardrails/console. Tools as Lambda functions.

**"I have a single agent and want fast deploy with multi-model flexibility."**
→ **AgentCore Harness**. Three API calls, per-invocation overrides, Bedrock + OpenAI + Gemini. **Single agents only.**

**"I need custom routing, human-in-the-loop, or local testing for multi-agent."**
→ **AgentCore + Custom Code**. Bring your Strands orchestrator, test locally, deploy to managed infra.

You don't pick once. Start on Harness, stretch with custom containers, graduate to Runtime when the loop itself is the limitation.

## Comparison Table

| | Bedrock Agents | AgentCore Harness | AgentCore + Custom |
|---|---|---|---|
| **Best for** | Managed agents, no-code teams | **Single agent**, fast iteration | Multi-agent at scale |
| **Tools** | Lambda functions | Gateway/MCP | Your code |
| **Prompt caching** | Not available | Check docs | Available |
| **Per-invocation overrides** | Redeploy to change | Model, tools, prompt per call | Full control in code |
| **Knowledge Base** | Built-in | Connect via Gateway | Integrate yourself |
| **Guardrails** | Built-in | Configure separately | Integrate yourself |
| **Multi-model** | Bedrock only | Bedrock, OpenAI, Gemini | Any model |
| **Multi-agent** | Supervisor/collaborator | **Not supported** | Deploy any orchestration |
| **Local testing** | Needs deployed agent | N/A — cloud | Run on port 8080 |
| **Migration** | N/A | Gateway wraps Lambdas | `agentcore import-agent` |
| **Status** | GA | Preview (4 regions) | GA |

## Getting Started

If you haven't built the multi-agent system yet, start with [Part 7](https://blog.srikanthethiraj.com/build-a-multi-agent-support-system-with-strands-agents-and-bedrock).

```bash
cd agentic-ai-system/agentcore-deploy
python agent_app.py  # Test locally on port 8080
agentcore deploy --agent-name ecommerce-support  # Deploy
```

## Tear Down

```bash
agentcore delete-runtime --agent-name ecommerce-support
```

For Bedrock Agents, delete agents and Lambda functions via console or API.

## What's Next

This is Part 8 of an ongoing series:

- **Part 1** — [Insurance Claim Processor](https://blog.srikanthethiraj.com/build-an-ai-powered-insurance-claim-processor-with-amazon-bedrock): Bedrock basics, prompt templates, simple RAG
- **Part 2** — [Financial Services AI Assistant](https://blog.srikanthethiraj.com/build-a-financial-services-ai-assistant-with-amazon-bedrock): benchmarking, circuit breakers, cross-region resilience
- **Part 3** — [Customer Feedback Pipeline](https://blog.srikanthethiraj.com/build-a-customer-feedback-pipeline-with-amazon-bedrock): multimodal data processing
- **Part 4** — [RAG Knowledge Base](https://blog.srikanthethiraj.com/build-a-rag-knowledge-base-with-amazon-bedrock-and-opensearch): vector stores, embeddings, document chunking
- **Part 5** — [Advanced Search & Retrieval](https://blog.srikanthethiraj.com/optimize-rag-search-with-hybrid-retrieval-and-reranking-on-aws): hybrid search, reranking, query expansion
- **Part 6** — [AI Support Assistant](https://blog.srikanthethiraj.com/build-an-ai-support-assistant-with-bedrock-guardrails-and-governance): guardrails, prompt management, conversation flows
- **Part 7** — [Multi-Agent Support System](https://blog.srikanthethiraj.com/build-a-multi-agent-support-system-with-strands-agents-and-bedrock): Strands Agents, multi-agent orchestration
- **Part 8** — Deploy AI Agents on AWS (this post): Bedrock Agents vs AgentCore
- **Part 9** — Multi-Tier Model Deployment & Enterprise Integration
- **Part 10** — AI Safety — Guardrails, PII Protection & Threat Detection
- **Part 11** — Cost & Latency Optimization for GenAI
- **Part 12** — AI Governance — Compliance, Fairness & Model Cards
- **Part 13** — Testing, Evaluation & Troubleshooting GenAI Systems

Repository: [github.com/srikanthethiraj/agentic-ai-system](https://github.com/srikanthethiraj/agentic-ai-system)

---

*I'm Srikanth — a cloud engineer at AWS based in Austin, Texas. I learn by building, and I write about what I build. Follow along on this blog or connect with me on [LinkedIn](https://www.linkedin.com/in/srikanthethiraj/).*
