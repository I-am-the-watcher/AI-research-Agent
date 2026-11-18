import time
import requests
import streamlit as st

API = "http://localhost:8000"
st.set_page_config(page_title="Research Agent", layout="wide")
st.title("Autonomous Research Agent")

q = st.text_area("Research question", placeholder="e.g. How effective are 4-day work weeks on productivity?")
if st.button("Run research", disabled=not q.strip()):
    run_id = requests.post(f"{API}/research", json={"question": q}).json()["run_id"]
    status = st.status("Starting...", expanded=True)
    while True:
        run = requests.get(f"{API}/research/{run_id}").json()
        status.update(label=f"Stage: {run.get('stage') or 'queued'}")
        if run["status"] in ("completed", "failed"):
            break
        time.sleep(3)
    if run["status"] == "failed":
        st.error(run["error"])
    else:
        status.update(label="Done", state="complete")
        st.markdown(run["report"])
        v = run.get("verification") or {}
        with st.expander(f"Conflicts detected ({len(v.get('conflicts', []))})"):
            for c in v.get("conflicts", []):
                st.write(f"**{c['topic']}** - sources {c['source_ids']}: {c['explanation']}")
        with st.expander(f"Evidence ({len(run.get('findings') or [])} verified claims)"):
            for f in run.get("findings") or []:
                st.write(f"- {f['statement']}  \n  _\"{f['quote']}\"_ - {f['url']}")
