"""Agent Black Box Recorder
Records every model step and tool call of an agent run to a JSON file,
then replays a run or diffs two runs to find where they diverged.

Usage:
  python blackbox.py run "What is the total cost of 3 laptops and 2 pens?"
  python blackbox.py replay runs/<file>.json
  python blackbox.py diff runs/<a>.json runs/<b>.json
"""
import json
import os
from pathlib import Path
import re
import sys
import time

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

MAX_STEPS = 8

TOOLS = [
    {
        "name": "calculator",
        "description": "Evaluate a basic math expression like '3*900+2*1'.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "name": "lookup_price",
        "description": "Get the price in USD of one item (apple, laptop, pen).",
        "input_schema": {
            "type": "object",
            "properties": {"item": {"type": "string"}},
            "required": ["item"],
        },
    },
]

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"],
        },
    }
    for t in TOOLS
]

PRICES = {"apple": 2, "laptop": 900, "pen": 1}


def run_tool(name: str, args: dict) -> str:
    if name == "calculator":
        expr = args.get("expression", "")
        if not re.fullmatch(r"[0-9+\-*/(). ]+", expr):
            return "ERROR: invalid expression"
        try:
            return str(eval(expr, {"__builtins__": {}}))
        except Exception as e:
            return f"ERROR: {e}"
    if name == "lookup_price":
        item = str(args.get("item", "")).lower().rstrip("s")
        return str(PRICES[item]) if item in PRICES else "ERROR: unknown item"
    return "ERROR: unknown tool"


# ---------- RECORD ----------
def run_agent(task: str) -> str:
    messages = [{"role": "user", "content": task}]
    steps = []
    for _ in range(MAX_STEPS):
        if PROVIDER == "groq":
            r = client.chat.completions.create(
                model=MODEL, max_tokens=500, tools=GROQ_TOOLS, messages=messages
            )
            choice = r.choices[0]
            msg = choice.message
            messages.append(msg)
            text = msg.content or ""
            raw_calls = msg.tool_calls or []
            tool_calls = []
            parsed_calls = []
            for c in raw_calls:
                call_args = (
                    json.loads(c.function.arguments)
                    if isinstance(c.function.arguments, str)
                    else c.function.arguments
                )
                tool_calls.append({"name": c.function.name, "input": call_args})
                parsed_calls.append((c.id, c.function.name, call_args))

            steps.append(
                {
                    "type": "model",
                    "text": text,
                    "tool_calls": tool_calls,
                }
            )
            if not parsed_calls:
                break
            for call_id, name, args in parsed_calls:
                out = run_tool(name, args)
                steps.append(
                    {"type": "tool", "name": name, "input": args, "output": out}
                )
                messages.append(
                    {"role": "tool", "tool_call_id": call_id, "content": out}
                )
        else:
            r = client.messages.create(
                model=MODEL, max_tokens=500, tools=TOOLS, messages=messages
            )
            messages.append({"role": "assistant", "content": r.content})
            text = " ".join(b.text for b in r.content if b.type == "text")
            calls = [b for b in r.content if b.type == "tool_use"]
            steps.append(
                {
                    "type": "model",
                    "text": text,
                    "tool_calls": [{"name": c.name, "input": c.input} for c in calls],
                }
            )
            if not calls:
                break
            results = []
            for c in calls:
                out = run_tool(c.name, c.input)
                steps.append(
                    {"type": "tool", "name": c.name, "input": c.input, "output": out}
                )
                results.append(
                    {"type": "tool_result", "tool_use_id": c.id, "content": out}
                )
            messages.append({"role": "user", "content": results})

    os.makedirs("runs", exist_ok=True)
    path = f"runs/run_{int(time.time())}.json"
    with open(path, "w") as f:
        json.dump({"task": task, "steps": steps}, f, indent=2)
    final_text = next(
        (s["text"] for s in reversed(steps) if s["type"] == "model" and s["text"]),
        "(no response)",
    )
    print(f"Final answer: {final_text}\nRecorded -> {path}")
    return path


# ---------- REPLAY ----------
def describe(step: dict) -> str:
    if step["type"] == "model":
        calls = ", ".join(f"{c['name']}({c['input']})" for c in step["tool_calls"])
        return f"MODEL  said: {step['text'][:100]!r}  calls: [{calls}]"
    flag = "  <-- FAILED" if step["output"].startswith("ERROR") else ""
    return f"TOOL   {step['name']}({step['input']}) = {step['output']}{flag}"


def replay(path: str):
    run = json.load(open(path))
    print(f"Task: {run['task']}\n")
    for i, s in enumerate(run["steps"]):
        print(f"{i:>2}. {describe(s)}")


# ---------- DIFF ----------
def signature(step: dict):
    """What counts as 'same' between two steps (ignores free-text wording)."""
    if step["type"] == "model":
        return ("model", json.dumps(step["tool_calls"], sort_keys=True))
    return ("tool", step["name"], json.dumps(step["input"], sort_keys=True), step["output"])


def diff(path_a: str, path_b: str):
    a, b = json.load(open(path_a)), json.load(open(path_b))
    print(f"A task: {a['task']}\nB task: {b['task']}\n")
    for i in range(max(len(a["steps"]), len(b["steps"]))):
        sa = a["steps"][i] if i < len(a["steps"]) else None
        sb = b["steps"][i] if i < len(b["steps"]) else None
        if sa is None or sb is None or signature(sa) != signature(sb):
            print(f"First divergence at step {i}:")
            print("  A:", describe(sa) if sa else "(run ended)")
            print("  B:", describe(sb) if sb else "(run ended)")
            return
    print("Runs are identical in every tool call and result.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "run" and len(sys.argv) > 2:
        run_agent(" ".join(sys.argv[2:]))
    elif cmd == "replay" and len(sys.argv) == 3:
        replay(sys.argv[2])
    elif cmd == "diff" and len(sys.argv) == 4:
        diff(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
