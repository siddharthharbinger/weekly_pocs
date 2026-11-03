# POC 08: Claim-Level Evidence Compiler

Atomic claims -> evidence retrieval -> judgment -> provenance manifest.

## Implementation

Offline mode uses conservative exact matching. Live mode uses Groq for claim extraction (omit claims from input) and support/contradiction judgment. Source IDs and verbatim quotes are checked; unsupported claims are excluded from supported_answer.

## Run from repository root

```powershell
python -m pip install -r requirements-lab.txt
python -m poc_lab 08
python 08-evidence-compiler/run.py --input 08-evidence-compiler/sample.json --output reports/08.json

python -m poc_lab 08 --live --env-file "path/to/.env"
```

Edit sample.json or pass a separate JSON scenario. Reports go to stdout and optionally --output. No frontend or server. Shared implementation lives in `poc_lab/`. Offline demos do not make API calls.

## Limits

Lexical top-three retrieval can miss evidence. Valid quotations do not prove entailment. Model judgments can be wrong; this is not independent fact verification. NLI and learned embeddings are future extensions.

## Validation

Run `python -m pytest -q` from the repository root. Tests cover failure cases as well as successful execution. These are prototype experiments, not production-tested systems.
