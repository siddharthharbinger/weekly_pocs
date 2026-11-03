# Weekly POCs: AI Engineering Proof of Concepts

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Groq & Anthropic Compatible](https://img.shields.io/badge/LLM-Groq%20%7C%20Anthropic-orange.svg)](https://console.groq.com)

A curated collection of focused, lightweight, and experimental Proof of Concepts (POCs) solving critical challenges in building reliable, cost-efficient, and secure LLM applications.

Each POC is self-contained with its own runnable script, isolated architecture diagram, and deep-dive documentation.

---

## 🗺️ System Overview & POC Taxonomy

```mermaid
flowchart TB
    subgraph Reliability ["1. Retrieval & Epistemic Confidence"]
        POC1["01-rag-confidence<br/><b>Disagreement-Based RAG Confidence</b><br/><i>Contradiction detection across chunks & abstention gating</i>"]
    end

    subgraph MemoryHygiene ["2. State & Memory Management"]
        POC2["02-memory-auditor<br/><b>Long-Term Memory Rot Auditor</b><br/><i>Temporal staleness, duplicate purging & contradiction audit</i>"]
    end

    subgraph AgentObservability ["3. Agent Observability & Determinism"]
        POC3["03-blackbox-recorder<br/><b>Agent Black Box Recorder</b><br/><i>Flight recorder JSON traces, step replay & diff divergence detector</i>"]
    end

    subgraph Security ["4. Adversarial Red Teaming & Security"]
        POC4["04-injection-canary<br/><b>Prompt Injection Canary</b><br/><i>Canary trap tokens, tripwire detection & benchmark evaluation</i>"]
    end

    subgraph CostLatency ["5. Economics & Inference Routing"]
        POC5["05-model-router<br/><b>Cost-Aware Model Router</b><br/><i>Query complexity classification, dynamic tier dispatch & cost savings</i>"]
    end

    style POC1 fill:#2b6cb0,stroke:#2c5282,color:#fff
    style POC2 fill:#6b46c1,stroke:#553c9a,color:#fff
    style POC3 fill:#285e61,stroke:#234e52,color:#fff
    style POC4 fill:#9b2c2c,stroke:#742a2a,color:#fff
    style POC5 fill:#2f855a,stroke:#276749,color:#fff
```

---

## 📚 POC Catalog

| # | Directory & POC Name | Core Challenge Addressed | Architectural Pattern | Key Metric / Output |
|---|----------------------|--------------------------|-----------------------|---------------------|
| **01** | [`01-rag-confidence`](./01-rag-confidence/) | Inconsistent/conflicting documents in RAG knowledge bases | Isolated per-chunk generation + LLM consensus judging | Calibrated Confidence Score & Abstention Gating |
| **02** | [`02-memory-auditor`](./02-memory-auditor/) | Long-term memory rot, stale timestamps, conflicting facts | Temporal grounding + Multi-class semantic defect analysis | Memory Health Score % & Actionable Cleanup Plan |
| **03** | [`03-blackbox-recorder`](./03-blackbox-recorder/) | Agent non-determinism & silent multi-turn tool failures | Structured JSON flight recording, replay & diffing | Step-by-step Trace & First-Divergence Point |
| **04** | [`04-injection-canary`](./04-injection-canary/) | Indirect prompt injection via untrusted third-party data | Dynamic canary tokens + Tripwire tool invocation alerts | Empirical Defense Success Delta (e.g. 0% vs 100%) |
| **05** | [`05-model-router`](./05-model-router/) | Overspending on frontier models for trivial user tasks | Low-latency complexity classification + Cascading routing | % Cost Savings & Substance Parity Score |

---

## 📁 Repository Structure

```text
weekly_pocs/
├── .env.example                  # Template for required API keys
├── .gitignore                    # Excludes .env, virtual environments, caches
├── requirements.txt              # Core dependencies (groq, anthropic, dotenv, openai)
├── README.md                     # Root project documentation & taxonomy
├── 01-rag-confidence/
│   ├── README.md                 # Architecture, methodology & execution guide
│   └── rag_confidence.py         # Runnable implementation script
├── 02-memory-auditor/
│   ├── README.md                 # Architecture & memory scoring walkthrough
│   └── memory_auditor.py         # Runnable implementation script
├── 03-blackbox-recorder/
│   ├── README.md                 # Architecture, record/replay/diff documentation
│   ├── blackbox.py               # Runnable implementation script
│   └── runs/                     # Example serialized agent execution traces
│       └── run_1791263521.json
├── 04-injection-canary/
│   ├── README.md                 # Threat model, canary mechanics & defense benchmarks
│   └── injection_canary.py       # Runnable implementation script
└── 05-model-router/
    ├── README.md                 # Cost-quality optimization architecture
    └── model_router.py           # Runnable implementation script
```

---

## ⚡ Quickstart

### 1. Clone the Repository
```bash
git clone https://github.com/siddharthsavant27/weekly_pocs.git
cd weekly_pocs
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Credentials
Copy `.env.example` to `.env` and configure your API key:
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Groq (Default high-speed inference)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Anthropic (Optional fallback)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

---

## 🏃 Running the POCs

You can run each POC directly from its subfolder or from the root repository:

```bash
# POC 01: Disagreement-Based RAG Confidence
cd 01-rag-confidence
python rag_confidence.py "How many days do I have to get a refund?"

# POC 02: Memory Rot Auditor
cd ../02-memory-auditor
python memory_auditor.py

# POC 03: Agent Black Box Recorder
cd ../03-blackbox-recorder
python blackbox.py run "What is the total cost of 3 laptops and 2 pens?"
python blackbox.py replay runs/run_1791263521.json

# POC 04: Prompt Injection Canary
cd ../04-injection-canary
python injection_canary.py

# POC 05: Cost-Aware Model Router
cd ../05-model-router
python model_router.py
```

---

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## CLI Lab: POCs 06–11

Python 3.11+; no frontend. All six have offline demos, JSON inputs/reports, and regression tests.

- [06 — Agent Permission Drift Firewall](./06-permission-firewall/)
- [07 — Counterfactual Agent Simulator](./07-counterfactual-simulator/)
- [08 — Claim-Level Evidence Compiler](./08-evidence-compiler/)
- [09 — Temporal Blind-Spot Detector](./09-temporal-blindspot/)
- [10 — Semantic Cache Invalidation Engine](./10-semantic-cache/)
- [11 — Adaptive Reasoning Budget Controller](./11-reasoning-budget/)

### Setup and run

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-lab.txt
.venv/Scripts/python -m poc_lab 10
.venv/Scripts/python -m pytest -q
```

On macOS/Linux use `.venv/bin/python`. Run any number 06–11 with `python -m poc_lab NUMBER`.
Use `--input scenario.json --output reports/result.json` for custom experiments.
POCs 08, 09 and 11 support `--live --env-file path/to/.env`; this sends supplied text/frames to Groq.
Set GROQ_API_KEY and GROQ_MODEL; POC 09 also requires GROQ_VISION_MODEL or --model.
No API key is needed for offline tests. Keep .env local; never commit it.

POC 10 supports `--db cache.db` for persistence. Its default encoder is a lexical baseline.
POC 06 enforces explicit policies; 07 simulates only allowlisted account operations;
08 uses an exact-match offline baseline or Groq judgments; 09 uses visual changes;
11 uses an arithmetic verifier. See each README for limits and deferred extensions.

Groq API integration follows [text chat](https://console.groq.com/docs/text-chat)
and [vision](https://console.groq.com/docs/vision) documentation. Model availability is account-dependent.

### Evaluation

Run `python -m poc_lab.evaluate` for reproducible offline comparisons.
Recorded synthetic results are in [tests/evaluation-results.json](tests/evaluation-results.json).
These fixtures demonstrate behavior; they are not a general accuracy benchmark.
The initial Windows/Python 3.12 validation passed 22 tests. Live Groq smoke tests
for evidence judgment and arithmetic verification passed with `openai/gpt-oss-20b`.
