"""Memory Rot Auditor
Scans an AI assistant's long-term memory (one fact per line) for
duplicates, contradictions, and stale facts, then prints a cleanup report.

Run:  python memory_auditor.py                # uses the sample memory below
      python memory_auditor.py memory.txt     # your own file, one fact per line
"""
import json
import os
from pathlib import Path
import re
import sys
from datetime import date

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
    MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    PROVIDER = "anthropic"
else:
    print(f"Error: Missing API key. Please set GROQ_API_KEY in: {env_path}")
    sys.exit(1)

SAMPLE_MEMORY = [
    "User lives in Pune (noted 2022-03-10)",
    "User lives in Bangalore (noted 2024-08-02)",
    "User likes Python",
    "User's favorite language is Python",
    "User is preparing for the GATE exam in Feb 2023",
    "User is vegetarian",
    "User eats chicken on weekends",
    "User works at Acme Corp as an intern (noted 2023-01-15)",
]


def load_memory() -> list:
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            return [line.strip() for line in f if line.strip()]
    return SAMPLE_MEMORY


def audit(facts: list) -> list:
    numbered = "\n".join(f"{i}: {f}" for i, f in enumerate(facts))
    prompt = (
        f"Today is {date.today()}. Below are facts stored in an AI assistant's memory.\n"
        f"{numbered}\n\n"
        "Find problems of three types:\n"
        "- duplicate: facts that say the same thing\n"
        "- contradiction: facts that cannot both be true\n"
        "- stale: facts about past events/dates or likely outdated info\n"
        "Respond ONLY with a JSON list. Each item: "
        '{"type": "...", "ids": [ints], "reason": "...", "action": "keep <id> / delete <id> / merge"}. '
        "Return [] if memory is clean."
    )
    if PROVIDER == "groq":
        r = client.chat.completions.create(
            model=MODEL, max_tokens=1500, messages=[{"role": "user", "content": prompt}]
        )
        text = r.choices[0].message.content
    else:
        r = client.messages.create(
            model=MODEL, max_tokens=1500, messages=[{"role": "user", "content": prompt}]
        )
        text = r.content[0].text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    return json.loads(match.group(0)) if match else []


def main():
    facts = load_memory()
    issues = audit(facts)

    print(f"\nAudited {len(facts)} memories, found {len(issues)} issue(s).\n")
    flagged = set()
    for n, issue in enumerate(issues, 1):
        flagged.update(issue["ids"])
        print(f"{n}. [{issue['type'].upper()}] {issue['reason']}")
        for i in issue["ids"]:
            print(f"     #{i}: {facts[i]}")
        print(f"   Suggested: {issue['action']}\n")

    health = round(100 * (1 - len(flagged) / max(len(facts), 1)))
    print(f"Memory health score: {health}% ({len(flagged)}/{len(facts)} entries flagged)")


if __name__ == "__main__":
    main()
