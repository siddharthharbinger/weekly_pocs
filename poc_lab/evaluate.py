"""Small reproducible baseline comparisons. No API calls or invented model scores."""
import json
from .firewall import Firewall
from .simulator import run as simulate
from .cache import Cache
from .evidence import run as evidence
from .video import run as video
from .budget import run as reason


def evaluate():
    correct = 0
    for i in range(100):
        gate = Firewall({'tools': ['read_ticket'], 'ticket_ids': ['T1']})
        authorized = i % 2 == 0
        action = {'tool': 'read_ticket', 'arguments': {'ticket_id': 'T1' if authorized else 'T2'}}
        correct += (gate.check(action)['decision'] == 'allow') == authorized
    simulation = simulate({'balances': {1: 100, 2: 50},
                           'changes': [{'account_id': 1, 'delta': -101}, {'account_id': 2, 'delta': 101}]})
    cache = Cache()
    try:
        cache.update_source('policy', '7 days')
        cache.put('delivery time', '7 days', ['policy'])
        before = cache.get('delivery time')
        cache.update_source('policy', '5 days')
        after = cache.get('delivery time')
    finally:
        cache.close()
    evidence_report = evidence({'claims': ['Linux is supported.', 'Offline mode exists.'],
                                'sources': [{'id': 'docs', 'text': 'Linux is supported.'}]})
    v = video({})
    adaptive = reason({'a': 10, 'b': 5, 'candidate_answers': ['14', '15']})
    fixed = reason({'a': 10, 'b': 5, 'candidate_answers': ['14'], 'budget': {'calls': 1}})
    return {
        'scope': 'synthetic offline fixtures; not estimates of real-world accuracy',
        '06': {'cases': 100, 'correct': correct, 'allow_all_correct': 50},
        '07': {'unsafe_action_flagged': simulation['decision'] == 'review', 'execute_without_check_would_overdraw': True},
        '08': {'claims': 2, 'flagged': evidence_report['unsupported_count'], 'unchecked_answer_flags': 0},
        '09': {'uniform_event_covered': any(13 <= i <= 15 for i in v['uniform_frames']),
               'adaptive_event_covered': any(13 <= i <= 15 for i in v['extra_frames']),
               'uniform_frames': len(v['uniform_frames']), 'adaptive_frames': v['selected_count']},
        '10': {'naive_cache_would_return': before['answer'], 'dependency_cache_hit_after_update': after is not None},
        '11': {'one_shot_verified': fixed['verified'], 'adaptive_verified': adaptive['verified'], 'adaptive_calls': adaptive['calls']},
    }


if __name__ == '__main__':
    print(json.dumps(evaluate(), indent=2))
