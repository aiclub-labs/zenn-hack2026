"""
Minimal Streamlit UI — upload + approval loop skeleton.

Theme-agnostic: shows the three reusable patterns (upload, agent-progress,
human-approval) that any of the candidate agents will need.
"""
import httpx
import streamlit as st

API_URL = st.sidebar.text_input("API URL", value="http://localhost:8000")

st.title("Agent Baseline — Upload + Approval Loop")

# 1. Upload (artifact-agnostic; accept anything for now)
uploaded = st.file_uploader("Upload an artifact", type=None)
if uploaded is not None:
    st.info(f"Received `{uploaded.name}` ({uploaded.size} bytes). "
            "Swap to theme-specific handler once problem is frozen.")

# 2. Agent progress (placeholder — reuse for Scanner / Planner output)
if st.button("Run baseline ping"):
    with st.spinner("Calling /chat …"):
        try:
            r = httpx.post(f"{API_URL}/chat", json={"message": "hello"}, timeout=30)
            st.success(r.json().get("reply", "no reply"))
        except Exception as e:
            st.error(f"Call failed: {e}")

# 3. Human-in-the-loop approval pattern (skeleton)
st.divider()
st.subheader("Approval pattern (skeleton)")
proposed = st.session_state.setdefault("proposed_changes", [
    {"id": 1, "description": "Example: normalize font on slide 3"},
    {"id": 2, "description": "Example: align heading on slide 7"},
])
approvals = {c["id"]: st.checkbox(c["description"], key=f"app_{c['id']}") for c in proposed}
if st.button("Apply approved changes"):
    approved = [cid for cid, ok in approvals.items() if ok]
    st.write(f"Would apply {len(approved)} change(s): {approved}")
