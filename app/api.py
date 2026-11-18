from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from . import db
from .graph import run_research


@asynccontextmanager
async def lifespan(_):
    db.init_db()
    yield


app = FastAPI(title="Autonomous Research Agent", lifespan=lifespan)


class Query(BaseModel):
    question: str


def execute(run_id: str, question: str):
    try:
        state = run_research(question, on_stage=lambda s: db.set_stage(run_id, s))
        db.finish_run(run_id, state)
    except Exception as e:  # keep failures visible instead of silent
        db.fail_run(run_id, repr(e))


@app.post("/research", status_code=202)
def start(q: Query, bg: BackgroundTasks):
    run_id = db.create_run(q.question)
    bg.add_task(execute, run_id, q.question)
    return {"run_id": run_id}


@app.get("/research/{run_id}")
def get(run_id: str):
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(404, "run not found")
    return run

@app.get("/usage")
def usage():
    from .config import TAVILY_MONTHLY_LIMIT
    return {"tavily_credits_used": db.tavily_usage(), "limit": TAVILY_MONTHLY_LIMIT}