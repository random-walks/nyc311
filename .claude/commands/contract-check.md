---
description:
  Audit the current branch for drift between nyc311's factor-factory bridge and
  the upstream factor-factory API. Invokes the factor-compat-auditor agent.
---

Invoke the
[`factor-compat-auditor`](../agents/factor-compat-auditor.md) agent against
`git diff origin/main...HEAD`. Relay its report verbatim; do not summarize or
editorialize. If the agent flags a blocking item, print the agent's
remediation hint and stop — do not attempt fixes yourself.

If the agent returns a clean report, also print:

```
Contract check clean. Proceed with the PR when preflight is green:
  make ci
  uv run --frozen mkdocs build --strict
  .venv/bin/python -m pytest tests/test_factor_factory_adapter.py tests/test_factor_factory_engines.py -v
```

Do NOT modify code, do NOT commit, do NOT push.
