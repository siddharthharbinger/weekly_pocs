# POC 09: Temporal Blind-Spot Detector

Video frames -> low-resolution change scores -> uniform + adaptive frame selection.

## Implementation

The demo generates a short event between uniform samples. Real video is supported with a video path in JSON. A cheap scan of every frame selects a bounded number of extra frames; live mode captions selected frames using Groq vision.

## Run from repository root

```powershell
python -m pip install -r requirements-lab.txt
python -m poc_lab 09
python 09-temporal-blindspot/run.py --input 09-temporal-blindspot/sample.json --output reports/09.json

python -m poc_lab 09 --live --env-file "path/to/.env"
```

Edit sample.json or pass a separate JSON scenario. Reports go to stdout and optionally --output. No frontend or server. Shared implementation lives in `poc_lab/`. Offline demos do not make API calls.

## Limits

Motion is only a proxy for evidence gaps. Camera motion creates false positives and static semantic changes may be missed. Every frame is decoded; savings concern expensive vision inference, not decoding. Captioning is not a validated event classifier.

## Validation

Run `python -m pytest -q` from the repository root. Tests cover failure cases as well as successful execution. These are prototype experiments, not production-tested systems.
