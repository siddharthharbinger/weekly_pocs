# POC 07: Counterfactual Agent Simulator

Account balances + proposed changes -> isolated SQLite simulation -> invariant report.

## Implementation

A database backup creates a disposable state copy. Checks cover negative balances, conservation, affected-record limits and missing accounts. Original state remains unchanged.

## Run from repository root

```powershell
python -m pip install -r requirements-lab.txt
python -m poc_lab 07
python 07-counterfactual-simulator/run.py --input 07-counterfactual-simulator/sample.json --output reports/07.json
```

Edit sample.json or pass a separate JSON scenario. Reports go to stdout and optionally --output. No frontend or server. Shared implementation lives in `poc_lab/`. Offline demos do not make API calls.

## Limits

Controlled integer-cent account updates only. No arbitrary code, SQL, Docker execution, external systems or real-action execution. Simulation results cover only declared invariants.

## Validation

Run `python -m pytest -q` from the repository root. Tests cover failure cases as well as successful execution. These are prototype experiments, not production-tested systems.
