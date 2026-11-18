"""PostgreSQL persistence for runs, reports and evidence."""
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json
from .config import DATABASE_URL


def _conn():
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)


def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS runs (
                 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                 question text NOT NULL,
                 status text NOT NULL DEFAULT 'running',
                 stage text,
                 report text,
                 sources jsonb,
                 findings jsonb,
                 verification jsonb,
                 error text,
                 created_at timestamptz DEFAULT now())"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS tavily_usage (
                 month text PRIMARY KEY,
                 credits int NOT NULL DEFAULT 0)"""
        )


def create_run(question: str) -> str:
    with _conn() as c:
        return str(c.execute("INSERT INTO runs (question) VALUES (%s) RETURNING id", (question,)).fetchone()["id"])


def set_stage(run_id: str, stage: str):
    with _conn() as c:
        c.execute("UPDATE runs SET stage=%s WHERE id=%s", (stage, run_id))


def finish_run(run_id: str, state: dict):
    with _conn() as c:
        c.execute(
            "UPDATE runs SET status='completed', stage='done', report=%s, sources=%s, findings=%s, verification=%s WHERE id=%s",
            (
                state.get("report"),
                Json(state.get("sources", [])),
                Json([f.model_dump() for f in state.get("findings", [])]),
                Json(state["verification"].model_dump() if state.get("verification") else None),
                run_id,
            ),
        )


def fail_run(run_id: str, error: str):
    with _conn() as c:
        c.execute("UPDATE runs SET status='failed', error=%s WHERE id=%s", (error, run_id))


def get_run(run_id: str):
    with _conn() as c:
        r = c.execute("SELECT * FROM runs WHERE id=%s", (run_id,)).fetchone()
    if r:
        r["id"], r["created_at"] = str(r["id"]), str(r["created_at"])
    return r

def tavily_usage() -> int:
    """Credits used so far this calendar month."""
    with _conn() as c:
        row = c.execute(
            "SELECT credits FROM tavily_usage WHERE month = to_char(now(), 'YYYY-MM')"
        ).fetchone()
    return row["credits"] if row else 0


def add_tavily_usage(n: int) -> int:
    with _conn() as c:
        row = c.execute(
            """INSERT INTO tavily_usage (month, credits)
               VALUES (to_char(now(), 'YYYY-MM'), %s)
               ON CONFLICT (month) DO UPDATE SET credits = tavily_usage.credits + %s
               RETURNING credits""",
            (n, n),
        ).fetchone()
    return row["credits"]
