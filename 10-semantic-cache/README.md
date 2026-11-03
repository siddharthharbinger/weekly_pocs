# POC 10: Semantic Cache Invalidation Engine

Source updates -> explicit answer dependencies -> selective invalidation.

## Implementation

SQLite persists cached answers and source hashes. Source changes delete dependent answers transactionally. Reordering query words demonstrates cosine retrieval; an encoder interface allows later learned embeddings.

## Run from repository root

```powershell
python -m pip install -r requirements-lab.txt
python -m poc_lab 10
python 10-semantic-cache/run.py --input 10-semantic-cache/sample.json --output reports/10.json
```

Edit sample.json or pass a separate JSON scenario. Reports go to stdout and optionally --output. No frontend or server. Shared implementation lives in `poc_lab/`. Offline demos do not make API calls.

## Limits

Default retrieval is lexical, not learned semantic similarity. Dependencies must be supplied completely by the caller. No automatic source watching, tenant isolation, source deletion API or cross-process freshness guarantee.

## Validation

Run `python -m pytest -q` from the repository root. Tests cover failure cases as well as successful execution. These are prototype experiments, not production-tested systems.
