"""The three agents: Planner, Researcher, Analyst (verifier + writer)."""
import re
from .llm import structured, text
from .models import Plan, Extraction, Finding, Verification, SubTask
from .tools import web_search, credibility
from .config import MAX_SUBTASKS
from . import rag

# ---------------------------------------------------------------- Planner
PLANNER_SYS = (
    "You are a research planner. Break the question into independent, searchable sub-tasks. "
    "Each query must be short and specific. Cover different angles (definitions, data, "
    "opposing views, recent developments). Never answer the question yourself."
)


def planner(state):
    it = state.get("iteration", 0)
    q = state["question"]
    if it == 0:
        plan = structured(
            PLANNER_SYS,
            f"Research question: {q}\nCreate at most {MAX_SUBTASKS} sub-tasks.",
            Plan,
        )
    else:  # follow-up round: only target the gaps found by the verifier
        gaps = "\n".join(f"- {g}" for g in state["verification"].gaps)
        plan = structured(
            PLANNER_SYS,
            f"Research question: {q}\nThese gaps remain after the first round:\n{gaps}\n"
            f"Create one new sub-task per gap (max {MAX_SUBTASKS}).",
            Plan,
        )
    # Hard cap: the model can ignore a prompt, but it can't ignore this slice
    tasks = [
        SubTask(id=f"r{it}-{n}", query=t.query, purpose=t.purpose)
        for n, t in enumerate(plan.subtasks)
    ][:MAX_SUBTASKS]
    return {"plan": state.get("plan", plan), "pending": tasks, "iteration": it + 1}


# ------------------------------------------------------------- Researcher
EXTRACT_SYS = (
    "Extract factual claims that help answer the sub-task, using ONLY the provided text. "
    "For each claim give a one-sentence statement and a short VERBATIM quote (max 25 words) "
    "copied exactly from the text. Return an empty list if nothing is relevant."
)


def _norm(s: str) -> str:
    return re.sub(r"\W+", " ", s).lower().strip()


def researcher(payload):
    """Runs once per sub-task, in parallel (LangGraph Send fan-out)."""
    task: SubTask = payload["task"]
    results = [
        r for r in web_search(task.query)
        if len(r.get("raw_content") or r.get("content") or "") > 200
    ]
    docs = [(r.get("raw_content") or r["content"])[:20000] for r in results]
    top = rag.select(task.query, docs)  # RAG: keep only relevant chunks

    findings = []
    for r, full_text, chunks in zip(results, docs, top):
        ex = structured(
            EXTRACT_SYS,
            f"Sub-task: {task.query} ({task.purpose})\n\nText:\n" + "\n---\n".join(chunks),
            Extraction,
        )
        cred = credibility(r["url"], r.get("score", 0.5))
        for c in ex.claims:
            # Source verification: drop claims whose quote isn't really in the page
            if _norm(c.quote) and _norm(c.quote) in _norm(full_text):
                findings.append(
                    Finding(
                        task_id=task.id,
                        url=r["url"],
                        title=r.get("title", r["url"]),
                        statement=c.statement,
                        quote=c.quote,
                        credibility=cred,
                    )
                )
    return {"findings": findings}


# --------------------------------------------------------------- Analyst
def source_index(findings) -> dict[str, int]:
    order: dict[str, int] = {}
    for f in findings:
        order.setdefault(f.url, len(order) + 1)
    return order


VERIFY_SYS = (
    "You are a skeptical research analyst. Given numbered evidence, (1) list claims corroborated "
    "by 2+ different sources, (2) list conflicts where sources disagree (cite source ids as integers), "
    "(3) list gaps: important aspects of the question with no or weak evidence. "
    "Weigh source credibility. Be conservative; return an empty gaps list if coverage is good."
)


def verifier(state):
    findings = state.get("findings", [])
    idx = source_index(findings)
    lines = [
        f'[S{idx[f.url]}] (cred {f.credibility}) {f.statement} | "{f.quote}"'
        for f in findings
    ]
    v = structured(
        VERIFY_SYS,
        f"Question: {state['question']}\n\nEvidence:\n" + "\n".join(lines),
        Verification,
    )
    return {"verification": v}


WRITE_SYS = (
    "Write a structured markdown research report. Sections: Summary, Key Findings, "
    "Conflicting Evidence, Limitations. Every factual sentence must end with citations like [S1][S3]. "
    "Use ONLY the evidence given; if evidence is thin, say so. Do not write a Sources section."
)


def writer(state):
    findings = state.get("findings", [])
    idx = source_index(findings)
    ev = "\n".join(
        f"[S{idx[f.url]}] (cred {f.credibility}) {f.statement}" for f in findings
    ) or "(no evidence found)"
    v = state["verification"]
    report = text(
        WRITE_SYS,
        f"Question: {state['question']}\n\nEvidence:\n{ev}\n\nCorroborated:\n{v.corroborated}\n\n"
        f"Conflicts:\n{[c.model_dump() for c in v.conflicts]}\n\nGaps:\n{v.gaps}",
    )
    titles = {f.url: f.title for f in findings}
    creds = {f.url: f.credibility for f in findings}
    sources = [
        {"id": n, "url": u, "title": titles[u], "credibility": creds[u]}
        for u, n in idx.items()
    ]
    refs = "\n".join(
        f"- [S{s['id']}] [{s['title']}]({s['url']}) (credibility {s['credibility']})"
        for s in sources
    )
    return {"report": f"{report}\n\n## Sources\n{refs}", "sources": sources}