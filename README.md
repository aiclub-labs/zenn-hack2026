# Microsoft Agent Hackathon 2026 — Scaffold

Theme-agnostic scaffold for the hackathon project. The primary candidate is a PPT Polish Agent (see `../idea-shortlist.md` and `../ideation-workbook.md`), but nothing in this scaffold assumes that theme — pivot to the backup (Meeting → Action Agent) requires only swapping agents and tools, not infra or framework.

## Stack

- **Language**: Python 3.11
- **Agent framework**: Semantic Kernel (multi-agent via `AgentGroupChat`)
- **LLM**: Azure OpenAI (`gpt-4o-mini` default, escalate to `gpt-4o` when needed)
- **Integration protocol**: MCP (Model Context Protocol) — `mcp` Python SDK
- **API layer**: FastAPI
- **UI**: Streamlit (v1); React only as a stretch
- **Compute**: Azure Container Apps (scale-to-zero)
- **Secrets**: Azure Key Vault + local `.env`
- **Observability**: Application Insights via OpenTelemetry
- **IaC**: Bicep
- **CI**: GitHub Actions

## Layout

```
scaffold/
├── README.md                    # This file
├── pyproject.toml               # Python deps + tool config (ruff, mypy, pytest)
├── .env.example                 # Env vars contract
├── .gitignore
├── .devcontainer/
│   └── devcontainer.json        # Reproducible dev env (Python + Azure CLI + Bicep)
├── app/
│   ├── main.py                  # FastAPI entrypoint + /health + /chat
│   ├── agents/
│   │   └── hello_agent.py       # Minimal SK agent (swap per theme)
│   ├── mcp/
│   │   └── echo_server.py       # MCP server template (swap per theme)
│   └── config.py                # Settings via pydantic-settings
├── ui/
│   └── streamlit_app.py         # Upload + approval loop skeleton
├── infra/
│   ├── main.bicep               # Subscription-scoped IaC entry (orchestrates RGs + modules)
│   ├── main.parameters.json
│   ├── bicepconfig.json
│   └── modules/                 # resource-groups / shared / rbac / budget / policy
├── scripts/
│   └── dev.sh                   # Local dev convenience
├── .github/workflows/
│   └── ci.yml                   # Lint + test on push
└── tests/
    └── test_smoke.py            # Hello-world test
```

## Quickstart (local, no Azure needed yet)

```bash
# 1. Create venv
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# 2. Copy env template
cp .env.example .env
# Fill in AZURE_OPENAI_* once Azure account is ready

# 3. Run API locally
uvicorn app.main:app --reload

# 4. Run UI in another terminal
streamlit run ui/streamlit_app.py
```

## Azure deploy (blocked until Azure account is opened)

`main.bicep` is subscription-scoped and creates the 3 RGs itself (`rg-hack2026-{dev,shared,prod}`). See `../azure-setup.md` for the full TL;DR runbook + per-phase scripts under `scripts/` (provider registration, member objectId resolution, what-if preview, GitOps wiring) and `scripts/automation/` for browser-side portal flows.

```bash
# Option A — azd
azd env new hack2026
azd provision

# Option B — pure az CLI
az deployment sub create \
  --location swedencentral \
  --template-file infra/main.bicep \
  --parameters @infra/main.parameters.json
```

## What's NOT in the scaffold (theme-specific, added later)

- `python-pptx` and PPT operations tools (only if PPT Polish Agent confirmed)
- Azure AI Speech bindings (only if Meeting → Action Agent confirmed as backup pivot)
- Specific agent personas (Scanner / Style Arbiter / Cross-Page Coherence) — added after Week 1 Problem Statement freeze
