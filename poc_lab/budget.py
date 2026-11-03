"""Bounded answer revisions with a deterministic arithmetic verifier."""
import re
import time
from pydantic import BaseModel, Field


class Budget(BaseModel):
    calls: int = Field(default=3, ge=0, le=20)
    output_tokens: int = Field(default=256, ge=1)
    seconds: float = Field(default=30, gt=0)


def run(data, llm=None, clock=time.monotonic):
    budget = Budget.model_validate(data.get('budget', {}))
    a, b = int(data['a']), int(data['b'])
    expected = a+b
    start, trace, used = clock(), [], 0
    answers = iter(data.get('candidate_answers', []))
    reason, verified, answer = 'call_limit', False, None
    for _ in range(budget.calls):
        remaining = budget.seconds - (clock()-start)
        if remaining <= 0:
            reason = 'time_limit'
            break
        if llm:
            feedback = '' if not trace else 'Your previous answer failed verification. Recalculate.'
            answer, tokens = llm.complete(f'Compute {a} + {b}. Return only the integer. {feedback}',
                                          budget.output_tokens, timeout=min(30, remaining))
        else:
            answer = next(answers, str(expected))
            tokens = 0  # no fabricated API usage for fixtures
        used += tokens
        verified = bool(re.fullmatch(r'[+-]?\d+', answer.strip())) and int(answer.strip()) == expected
        trace.append({'answer': answer, 'verified': verified, 'usage_tokens': tokens})
        if clock()-start > budget.seconds:
            reason = 'time_limit'
            verified = False
            break
        if verified:
            reason = 'verified'
            break
    return {'answer': answer, 'verified': verified, 'stop_reason': reason, 'trace': trace,
            'calls': len(trace), 'usage_tokens': used, 'elapsed_seconds': clock()-start,
            'max_generated_tokens': budget.calls * budget.output_tokens}
