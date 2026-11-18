"""Orchestration layer (supervisor logic) built with LangGraph."""
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from .models import ResearchState
from .agents import planner, researcher, verifier, writer
from .config import MAX_ITERATIONS

try:
    from langfuse.decorators import observe
except ImportError:  # pragma: no cover
    def observe(*a, **k):
        return lambda f: f


def dispatch(state):
    """Supervisor decision 1: fan out one Researcher per sub-task, in parallel."""
    tasks = state.get("pending", [])
    if not tasks:
        return "verifier"
    return [Send("researcher", {"task": t, "question": state["question"]}) for t in tasks]


def after_verify(state):
    """Supervisor decision 2: research more, or write the report?"""
    if state["verification"].gaps and state["iteration"] < MAX_ITERATIONS:
        return "planner"
    return "writer"


def build_graph():
    g = StateGraph(ResearchState)
    g.add_node("planner", planner)
    g.add_node("researcher", researcher)
    g.add_node("verifier", verifier)
    g.add_node("writer", writer)
    g.add_edge(START, "planner")
    g.add_conditional_edges("planner", dispatch, ["researcher", "verifier"])
    g.add_edge("researcher", "verifier")  # waits for ALL parallel researchers
    g.add_conditional_edges("verifier", after_verify, ["planner", "writer"])
    g.add_edge("writer", END)
    return g.compile()


graph = build_graph()


@observe(name="research_run")
def run_research(question: str, on_stage=None) -> dict:
    """Stream node updates so the API can report progress; merge them into a final state."""
    final: dict = {}
    for chunk in graph.stream({"question": question, "findings": [], "iteration": 0}, stream_mode="updates"):
        for node, upd in chunk.items():
            if on_stage:
                on_stage(node)
            for k, v in (upd or {}).items():
                final[k] = final.get(k, []) + v if k == "findings" else v
    return final
