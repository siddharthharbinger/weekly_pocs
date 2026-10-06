"""Cost-Aware Model Router (Groq)
Classifies each query as EASY or HARD, routes EASY to gpt-oss-20b and HARD to
gpt-oss-120b, then compares total cost and answer quality against always using 120b.

Setup: pip install openai ; export GROQ_API_KEY=your_key
Run:   python model_router.py
"""
import os
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

# Load .env from current directory or parent directory
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
    print(f"Error: Missing API key. Please set GROQ_API_KEY in: {env_path}")
    sys.exit(1)

try:
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
except ImportError:
    from openai import OpenAI

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
    )

SMALL = "openai/gpt-oss-20b"
LARGE = "openai/gpt-oss-120b"
# USD per 1M tokens (input, output). Verify against Groq's pricing page before reporting.
PRICE = {SMALL: (0.075, 0.30), LARGE: (0.15, 0.60)}

QUERIES = [
    "What is the capital of Australia?",
    "Convert 5 kilometers to miles.",
    "Give a one-line definition of photosynthesis.",
    "Rewrite this politely: 'Send me the report now.'",
    "A train leaves at 3pm going 60 km/h; another leaves the same station at 4pm going 90 km/h. When does the second catch up?",
    "Write a Python function that finds the longest palindromic substring and explain its time complexity.",
    "Compare the trade-offs between microservices and a monolith for a 5-person startup.",
    "If all bloops are razzies and some razzies are lazzies, can we conclude some bloops are lazzies? Explain.",
]


def call(model: str, prompt: str, max_tokens: int = 1500):
    """Returns (answer_text, cost_in_usd)."""
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=max_tokens,
        extra_body={"reasoning_effort": "low"},
    )
    p_in, p_out = PRICE[model]
    cost = (r.usage.prompt_tokens * p_in + r.usage.completion_tokens * p_out) / 1e6
    return (r.choices[0].message.content or "").strip(), cost


def classify(query: str):
    """Small model decides difficulty. Defaults to HARD if unsure (safe choice)."""
    out, cost = call(
        SMALL,
        "Classify how difficult this question is for an AI.\n"
        "EASY = simple fact, short lookup, basic rewrite or conversion.\n"
        "HARD = multi-step reasoning, math, code, or nuanced analysis.\n"
        "Reply with exactly one word: EASY or HARD.\n\n"
        f"Question: {query}",
        max_tokens=300,
    )
    return ("EASY" if "EASY" in out.upper() and "HARD" not in out.upper() else "HARD"), cost


def same_quality(query: str, reference: str, candidate: str) -> bool:
    """Judge (120b) checks if the cheap answer matches the reference in substance."""
    out, _ = call(
        LARGE,
        f"Question: {query}\n\nReference answer:\n{reference}\n\nCandidate answer:\n{candidate}\n\n"
        "Is the candidate correct and equivalent in substance to the reference? "
        "Reply with exactly one word: YES or NO.",
        max_tokens=300,
    )
    return "YES" in out.upper()


def main():
    routed_cost = baseline_cost = 0.0
    good = 0

    print(f"{'#':<3}{'route':<7}{'quality':<9}query")
    for i, q in enumerate(QUERIES, 1):
        label, c_cls = classify(q)
        model = SMALL if label == "EASY" else LARGE
        routed_ans, c_ans = call(model, q)
        routed_cost += c_cls + c_ans  # router overhead counts against us

        if model == LARGE:
            # Same model as the baseline, so reuse the answer and its cost.
            baseline_cost += c_ans
            ok = True
        else:
            baseline_ans, c_base = call(LARGE, q)
            baseline_cost += c_base
            ok = same_quality(q, baseline_ans, routed_ans)  # judge cost not counted
        good += ok
        print(f"{i:<3}{label:<7}{'OK' if ok else 'WORSE':<9}{q[:60]}")

    savings = 100 * (1 - routed_cost / baseline_cost)
    print(f"\nAlways-120b cost : ${baseline_cost:.6f}")
    print(f"Routed cost      : ${routed_cost:.6f}  (includes classifier overhead)")
    print(f"Cost savings     : {savings:.1f}%")
    print(f"Quality retained : {good}/{len(QUERIES)} answers as good as 120b")


if __name__ == "__main__":
    main()
