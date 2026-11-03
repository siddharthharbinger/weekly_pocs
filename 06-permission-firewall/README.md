# POC 06: Agent Permission Drift Firewall

Approved policy + proposed tool calls -> stateful allow/block decisions.

## Implementation

A deterministic policy is the authority. Tools, record IDs, write fields, extra arguments and cumulative call counts are checked. The dispatch API demonstrates enforcement before handlers run.

## Run from repository root

```powershell
python -m pip install -r requirements-lab.txt
python -m poc_lab 06
python 06-permission-firewall/run.py --input 06-permission-firewall/sample.json --output reports/06.json
```

Edit sample.json or pass a separate JSON scenario. Reports go to stdout and optionally --output. No frontend or server. Shared implementation lives in `poc_lab/`. Offline demos do not make API calls.

## Limits

No automatic policy approval, MCP transport or general intent inference yet. Caller must route every tool call through dispatch. Human-reviewed policies are required; this is not a production security boundary.

## Validation

Run `python -m pytest -q` from the repository root. Tests cover failure cases as well as successful execution. These are prototype experiments, not production-tested systems.
