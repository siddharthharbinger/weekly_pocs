# POC 01: Disagreement-Based RAG Confidence

> An epistemic confidence estimation framework for Retrieval-Augmented Generation (RAG) that detects source contradictions and hallucinated consensus by evaluating per-chunk answer agreements.

---

## 📌 Problem Statement

Traditional RAG systems concatenate all retrieved chunks into a single prompt and instruct the LLM to synthesize an answer. When the knowledge base contains **conflicting documentation** (e.g., outdated 2023 policy vs. updated 2024 FAQ) or **sparse context**, this standard approach exhibits major vulnerabilities:
1. **Hallucinated Conciliation:** The LLM forces an ungrounded compromise between contradictory chunks.
2. **First-Token Bias:** The model arbitrarily anchors on whichever chunk appears first in the prompt context.
3. **Uncalibrated Confidence:** Standard RAG pipelines return an answer with 100% confidence even when internal sources vehemently disagree.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    UserQuery([User Question]) --> Retrieval[Keyword Overlap Retrieval]
    Retrieval -->|Top-K Chunks| Chunk1[Chunk 1: 2023 Handbook]
    Retrieval -->|Top-K Chunks| Chunk2[Chunk 2: 2024 FAQ]
    Retrieval -->|Top-K Chunks| Chunk3[Chunk 3: Warranty Doc]

    subgraph PerChunkAnswering [Isolated Per-Chunk Generation]
        Chunk1 --> LLM1["LLM Answer #1<br/>('within 30 days')"]
        Chunk2 --> LLM2["LLM Answer #2<br/>('within 14 days')"]
        Chunk3 --> LLM3["LLM Answer #3<br/>('NOT_FOUND')"]
    end

    LLM1 --> Filter[Filter Valid Answers]
    LLM2 --> Filter
    LLM3 --> Filter

    Filter -->|Found Answers| Judge[LLM Agreement Judge]
    
    subgraph ConfidenceScoring [Confidence Calculation Engine]
        Judge -->|"Agreement Score A ∈ [0.0, 1.0]"| Formula["Confidence = A × (0.5 + 0.5 × Coverage)"]
        Filter -->|"Coverage = Valid / Total"| Formula
    end

    Formula --> Decision{Confidence ≥ Threshold?}
    Decision -->|Yes (≥ 0.60)| OutputAnswer[✅ Deliver Consensus Answer]
    Decision -->|No (< 0.60)| Abstain[🛑 Abstain & Surface Conflict]

    style UserQuery fill:#2d3748,stroke:#4a5568,color:#fff
    style Decision fill:#f6ad55,stroke:#dd6b20,color:#000
    style OutputAnswer fill:#48bb78,stroke:#2f855a,color:#fff
    style Abstain fill:#f56565,stroke:#c53030,color:#fff
```

---

## ⚙️ How It Works

1. **Top-K Chunk Retrieval:** Retrieves the top $k$ documents matching the question using lexical overlap (can be swapped for dense vector embeddings).
2. **Isolated Single-Chunk Queries:** Prompts the model to answer the query solely using **one chunk at a time**. If a chunk lacks relevant info, the model responds with `NOT_FOUND`.
3. **Answer Filtering & Coverage:** Discards `NOT_FOUND` outputs and calculates a coverage ratio:
   $$\text{Coverage} = \frac{|\text{valid answers}|}{|\text{retrieved chunks}|}$$
4. **LLM Consensus Judge:** Prompts the LLM to inspect all non-empty answers and output structured JSON assessing semantic agreement ($0.0 = \text{contradict}$ to $1.0 = \text{identical}$):
   ```json
   {
     "agreement": 0.0,
     "consensus": ""
   }
   ```
5. **Confidence Calibration:** Computes a composite confidence score penalized by retrieval coverage:
   $$\text{Confidence} = \text{Agreement} \times \left(0.5 + 0.5 \times \text{Coverage}\right)$$
6. **Abstain Gate:** If confidence falls below `0.60`, the system explicitly **abstains** and displays the conflicting viewpoints rather than hallucinating a false answer.

---

## 🚀 Getting Started

### Prerequisites

Ensure you have your environment configured in the root `.env`:
```bash
GROQ_API_KEY=your_groq_api_key_here
# or
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Running the Script

```bash
# Run with default conflicting question
python rag_confidence.py

# Run with a custom question
python rag_confidence.py "How long does shipping take?"
```

---

## 📊 Example Output

### Case 1: Conflicting Sources (Abstention Triggered)

```text
Q: How many days do I have to get a refund?

[chunk 1] Refund policy (2023 handbook): customers may request a refund within 30 days of purchase.
   -> You have 30 days from the date of purchase to request a refund.
[chunk 2] Refund policy (2024 FAQ): refunds are only available within 14 days of purchase.
   -> You have 14 days from purchase to get a refund.
[chunk 3] Warranty: all devices include a 1-year limited warranty against defects.
   -> NOT_FOUND

Agreement: 0.0  Coverage: 0.67
Confidence: 0.0
ABSTAINING: sources disagree or are too thin to trust.
Conflicting answers: [
  'You have 30 days from the date of purchase to request a refund.',
  'You have 14 days from purchase to get a refund.'
]
```

### Case 2: Unanimous / High Agreement

```text
Q: How long is the device warranty?

Agreement: 1.0  Coverage: 0.33
Confidence: 0.67
ANSWER: All devices include a 1-year limited warranty against defects.
```
