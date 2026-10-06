"""Disagreement-Based RAG Confidence
Idea: answer the question separately from each retrieved chunk.
If the answers agree -> confident. If they disagree or are missing -> abstain.

Run:  python rag_confidence.py "How many days do I have to get a refund?"
"""
import json
import os
from pathlib import Path
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

# Load .env from current directory or parent directory
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize client: Groq (default) or Anthropic fallback
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    PROVIDER = "groq"
elif ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your_anthropic_api_key_here":
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    PROVIDER = "anthropic"
else:
    print(f"Error: Missing API key. Please set GROQ_API_KEY in: {env_path}")
    sys.exit(1)

THRESHOLD = 0.6

# Tiny knowledge base. Note the deliberately conflicting refund chunks.
DOCS = [
    "Refund policy (2023 handbook): customers may request a refund within 30 days of purchase.",
    "Refund policy (2024 FAQ): refunds are only available within 14 days of purchase.",
    "Shipping: standard delivery takes 3-5 business days within the country.",
    "Support hours: our team is available Monday to Friday, 9am to 6pm.",
    "Warranty: all devices include a 1-year limited warranty against defects.",
]


def llm(prompt: str, max_tokens: int = 300) -> str:
    if PROVIDER == "groq":
        r = client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.choices[0].message.content.strip()
    else:
        r = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text.strip()


def words(text: str) -> set:
    return set(re.findall(r"\w+", text.lower()))


def retrieve(question: str, k: int = 3) -> list:
    """Naive keyword-overlap retrieval (swap for embeddings later)."""
    q = words(question)
    ranked = sorted(DOCS, key=lambda d: len(q & words(d)), reverse=True)
    return ranked[:k]


def answer_from_chunk(question: str, chunk: str) -> str:
    return llm(
        f"Context:\n{chunk}\n\nQuestion: {question}\n"
        "Answer in one short sentence using ONLY the context. "
        "If the context does not answer it, reply exactly NOT_FOUND."
    )


def judge(question: str, answers: list) -> dict:
    """Ask the model how much the per-chunk answers agree."""
    numbered = "\n".join(f"{i + 1}. {a}" for i, a in enumerate(answers))
    out = llm(
        f"Question: {question}\nAnswers from different sources:\n{numbered}\n\n"
        "Rate how much these answers agree with each other from 0.0 (contradict) "
        "to 1.0 (identical meaning). Respond ONLY with JSON: "
        '{"agreement": <float>, "consensus": "<best answer or empty>"}'
    )
    match = re.search(r"\{.*\}", out, re.DOTALL)
    return json.loads(match.group(0)) if match else {"agreement": 0.0, "consensus": ""}


def main():
    question = " ".join(sys.argv[1:]) or "How many days do I have to get a refund?"
    chunks = retrieve(question)

    print(f"\nQ: {question}\n")
    answers = []
    for i, chunk in enumerate(chunks, 1):
        a = answer_from_chunk(question, chunk)
        answers.append(a)
        print(f"[chunk {i}] {chunk}\n   -> {a}")

    found = [a for a in answers if a != "NOT_FOUND"]
    if not found:
        print("\nConfidence: 0.00 -> I don't know (nothing relevant retrieved).")
        return

    verdict = judge(question, found)
    coverage = len(found) / len(answers)  # penalise chunks that had no answer
    confidence = round(float(verdict["agreement"]) * (0.5 + 0.5 * coverage), 2)

    print(f"\nAgreement: {verdict['agreement']}  Coverage: {coverage:.2f}")
    print(f"Confidence: {confidence}")
    if confidence >= THRESHOLD:
        print(f"ANSWER: {verdict['consensus']}")
    else:
        print("ABSTAINING: sources disagree or are too thin to trust.")
        print("Conflicting answers:", found)


if __name__ == "__main__":
    main()
