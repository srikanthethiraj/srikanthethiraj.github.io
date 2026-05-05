"""Data models for the Agentic AI System."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToolResult:
    """Result from a tool invocation."""
    tool_name: str
    result: dict = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class AgentResponse:
    """Response from an agent."""
    agent_name: str
    response: str
    tools_used: list[str] = field(default_factory=list)
    reasoning: str = ""
    latency_ms: float = 0.0
    model_id: str = ""


@dataclass
class RoutingDecision:
    """Decision from the supervisor agent."""
    target_agent: str
    reason: str
    confidence: float = 0.0
    needs_human_review: bool = False


@dataclass
class HumanReviewRequest:
    """Request for human review."""
    action: str
    context: str
    agent_name: str
    risk_level: str = "medium"
    approved: Optional[bool] = None
    reviewer_notes: str = ""
