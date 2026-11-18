"""Offline evaluation: run the agent on a benchmark set and score the reports.
Usage: python -m eval.run_eval
"""
import json, re
from urllib.parse import urlparse
from pydantic import BaseModel
from app.graph import run_research
from app.llm import structured

QUESTIONS = [
    "What are the main benefits and risks of intermittent fasting?",
    "How has solar panel cost changed over the last decade and why?",
    "Is remote work more productive than office work?",
]


class Judge(BaseModel):
    faithfulness: int   # 1-5: are claims supported by the evidence?
    completeness: int   # 1-5: does it answer the question and show conflicts?
    reasoning: str


JUDGE_SYS = ("You are a strict evaluator. Score the report 1-5 for faithfulness (every claim supported by "
             "the evidence list) and completeness. Penalise unsupported claims heavily.")


def score(question, state):
    report = state.get("report", "")
    n_src = len(state.get("sources", []))
    cited = {int(x) for x in re.findall(r"\[S(\d+)\]", report)}
    evidence = "\n".join(f"- {f.statement}" for f in state.get("findings", []))
    j = structured(JUDGE_SYS, f"Question: {question}\n\nEvidence:\n{evidence}\n\nReport:\n{report}", Judge)
    return {
        "question": question,
        "sources": n_src,
        "domains": len({urlparse(s["url"]).netloc for s in state.get("sources", [])}),
        "invalid_citations": len([c for c in cited if c > n_src]),   # hallucinated citation ids
        "citation_coverage": round(len(cited) / n_src, 2) if n_src else 0,
        "conflicts_found": len(state["verification"].conflicts) if state.get("verification") else 0,
        "faithfulness": j.faithfulness,
        "completeness": j.completeness,
    }


if __name__ == "__main__":
    rows = [score(q, run_research(q)) for q in QUESTIONS]
    for r in rows:
        print(r)
    json.dump(rows, open("eval/results.json", "w"), indent=2)
