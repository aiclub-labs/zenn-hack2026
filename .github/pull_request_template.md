## Summary

<!-- 1-3 bullets: what changed, why -->

## Scope

- [ ] App / agent code (`app/`)
- [ ] UI (`ui/`)
- [ ] Infra (`infra/`) — triggers `infra-ci.yml` what-if
- [ ] CI / workflows
- [ ] Docs only

## Test plan

- [ ] `ruff check .` passes
- [ ] `mypy app` passes
- [ ] `pytest -q` passes
- [ ] (If infra) what-if reviewed in CI run
- [ ] Manual smoke: `/health` returns ok

## Hackathon checklist

- [ ] Stays inside Microsoft AI + Azure compute mandates (no non-Azure compute, no non-Microsoft AI in shipped path)
- [ ] No secrets committed (`.env`, keys, connection strings)
- [ ] If touching cost-sensitive resources, budget impact noted

## Notes

<!-- Anything reviewers should know -->
