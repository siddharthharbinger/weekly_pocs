# POC 11: Adaptive Reasoning Budget Controller

Initial answer -> deterministic verifier -> bounded revision -> stop reason.

## Implementation

Arithmetic addition provides an independently checkable task. Offline candidates exercise retries; live mode calls Groq. Reports include actual token usage, calls, elapsed time and verification outcomes.

## Run from repository root

```powershell
python -m pip install -r requirements-lab.txt
python -m poc_lab 11
python 11-reasoning-budget/run.py --input 11-reasoning-budget/sample.json --output reports/11.json

python -m poc_lab 11 --live --env-file "path/to/.env"
```

Edit sample.json or pass a separate JSON scenario. Reports go to stdout and optionally --output. No frontend or server. Shared implementation lives in `poc_lab/`. Offline demos do not make API calls.

## Limits

Limits cap calls, per-call output and wall-clock request timeout; there is no hard aggregate input-token or dollar budget. Arithmetic is the only verifier. No hidden chain-of-thought is inspected. Broader tasks need task-specific verifiers.

## Validation

Run `python -m pytest -q` from the repository root. Tests cover failure cases as well as successful execution. These are prototype experiments, not production-tested systems.
