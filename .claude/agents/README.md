# Hackathon Subagents

Three specialists carve up the scaffold along orthogonal axes so two of them can work in parallel without clobbering each other.

| Agent | Owns | Hand off to |
|---|---|---|
| [`infra`](./infra.md) | `infra/`, `.github/workflows/infra-*.yml`, `azure.yaml`, deployment runbooks | `general-dev` for app config wiring; `genai-dev` for AOAI capacity asks |
| [`general-dev`](./general-dev.md) | `app/main.py`, `app/config.py`, `app/mcp/` (transport), `ui/`, `tests/`, `pyproject.toml`, `.devcontainer/`, `.github/workflows/ci.yml` | `infra` for resource shape; `genai-dev` for tool semantics + agent logic |
| [`genai-dev`](./genai-dev.md) | `app/agents/`, prompts, tool *semantics* in `app/mcp/<server>.py`, model selection, evals | `general-dev` for transport/UI; `infra` for AOAI Bicep + budget headroom |

## Canonical facts (every agent must respect)

- Project prefix: `hack2026`
- Region: `swedencentral`
- RGs: `rg-hack2026-{dev,shared,prod}` (subscription-scoped Bicep creates them)
- Compute: Azure Container Apps
- Default model: `gpt-4o-mini`; escalate to `gpt-4o` only for arbitration
- Budget: $180, alerts at 80% / 100%
- Framework: Semantic Kernel (Python) + MCP

If a request contradicts these, the receiving agent pushes back rather than silently propagating drift. Source of truth: `infra/main.bicep`, `infra/main.parameters.json`, `azure-setup.md`, `dev-prep.md` §9.

## How to invoke

From the scaffold project root:

```
@infra        # for Bicep / Azure CLI / RBAC / budget / OIDC questions
@general-dev  # for FastAPI / Streamlit / pyproject / tests / devcontainer
@genai-dev    # for SK agents / prompts / tool schemas / model + cost
```

The orchestrator (you) decides which to dispatch. Parallelize `infra` and either dev agent when the work is independent.
