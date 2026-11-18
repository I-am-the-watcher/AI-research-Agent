# Autonomous AI Research Agent

Planner -> parallel Researchers (Tavily + RAG) -> Analyst (verify, loop on gaps) -> cited report.

## Run
```bash
cp .env.example .env            # fill in keys
docker compose up -d            # PostgreSQL
pip install -r requirements.txt
uvicorn app.api:app --reload    # API on :8000
streamlit run ui/streamlit_app.py
python -m eval.run_eval         # offline evaluation
```
