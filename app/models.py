"""Typed data contracts + the shared LangGraph state."""
import operator
from typing import Annotated, TypedDict
from pydantic import BaseModel


class SubTask(BaseModel):
    id: str
    query: str      # a search-engine-friendly query
    purpose: str    # why this task matters for the question


class Plan(BaseModel):
    objective: str
    subtasks: list[SubTask]


class Claim(BaseModel):
    statement: str  # one factual claim, in the model's words
    quote: str      # verbatim supporting excerpt from the source


class Extraction(BaseModel):
    claims: list[Claim]


class Finding(BaseModel):
    task_id: str
    url: str
    title: str
    statement: str
    quote: str
    credibility: float


class Conflict(BaseModel):
    topic: str
    source_ids: list[int]
    explanation: str


class Verification(BaseModel):
    corroborated: list[str]     # claims backed by 2+ independent sources
    conflicts: list[Conflict]   # sources that disagree
    gaps: list[str]             # missing info -> triggers another research loop


class ResearchState(TypedDict, total=False):
    question: str
    plan: Plan
    pending: list[SubTask]
    # reducer: parallel researchers append to the same list instead of overwriting
    findings: Annotated[list[Finding], operator.add]
    verification: Verification
    iteration: int
    report: str
    sources: list[dict]
