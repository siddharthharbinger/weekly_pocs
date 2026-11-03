import json
import subprocess
import sys
from pathlib import Path
import pytest
from poc_lab.firewall import Firewall
from poc_lab.simulator import run as simulate
from poc_lab.cache import Cache
from poc_lab.evidence import run as evidence, Judgment
from poc_lab.video import run as video, select
from poc_lab.budget import run as reason

ROOT = Path(__file__).resolve().parents[1]


def test_firewall_blocks_scope_arguments_and_budget():
    gate = Firewall({'tools': ['read_ticket'], 'ticket_ids': ['1'], 'max_calls': 1})
    for action in [
        {'tool': 'update_ticket', 'arguments': {'ticket_id': '1'}},
        {'tool': 'read_ticket', 'arguments': {'ticket_id': '2'}},
        {'tool': 'read_ticket', 'arguments': {'ticket_id': '1', 'destination': 'external'}},
    ]:
        assert gate.check(action)['decision'] == 'block'
    valid = {'tool': 'read_ticket', 'arguments': {'ticket_id': '1'}}
    assert gate.check(valid)['decision'] == 'allow'
    assert gate.check(valid)['decision'] == 'block'


def test_blocked_dispatch_never_executes():
    gate = Firewall({'tools': [], 'ticket_ids': []})
    result = gate.dispatch({'tool': 'delete', 'arguments': {}}, {'delete': lambda: pytest.fail('executed')})
    assert result['decision'] == 'block'


def test_write_field_constraints():
    gate = Firewall({'tools': ['update_ticket'], 'ticket_ids': ['1'], 'writable_fields': ['summary']})
    assert gate.check({'tool': 'update_ticket', 'arguments': {'ticket_id': '1', 'fields': {'status': 'closed'}}})['decision'] == 'block'


@pytest.mark.parametrize('changes,decision', [
    ([{'account_id': 1, 'delta': -20}, {'account_id': 2, 'delta': 20}], 'allow'),
    ([{'account_id': 1, 'delta': -200}], 'review'),
    ([{'account_id': 99, 'delta': 0}], 'review'),
    ([{'account_id': 1, 'delta': 1}], 'review'),
])
def test_simulation_invariants(changes, decision):
    data = {'balances': {1: 100, 2: 50}, 'changes': changes}
    report = simulate(data)
    assert report['decision'] == decision
    assert report['source_unchanged']
    assert data['balances'] == {1: 100, 2: 50}


def test_cache_invalidation_is_selective_and_persistent(tmp_path):
    path = tmp_path / 'cache.db'
    c = Cache(path)
    c.update_source('shipping', '7 days')
    c.update_source('returns', '30 days')
    c.put('shipping time', '7 days', ['shipping'])
    c.put('return window', '30 days', ['returns'])
    assert c.get('time shipping')['answer'] == '7 days'
    assert c.update_source('shipping', '7 days') == []
    assert c.update_source('shipping', '5 days') == ['shipping time']
    c.close()
    c = Cache(path)
    assert c.get('shipping time') is None
    assert c.get('return window')['answer'] == '30 days'
    with pytest.raises(ValueError):
        c.put('q', 'a', ['missing'])
    c.close()


def test_evidence_abstains_without_evidence():
    result = evidence({'claims': ['Linux is supported.', 'Offline mode exists.'],
                       'sources': [{'id': 'docs', 'text': 'Linux is supported.'}]})
    assert [c['status'] for c in result['claims']] == ['supported', 'unknown']
    assert result['unsupported_count'] == 1


def test_fabricated_model_citation_is_rejected():
    class Fake:
        def structured(self, *args):
            return Judgment(status='supported', source_id='invented', quote='fiction')
    result = evidence({'claims': ['x'], 'sources': [{'id': 'real', 'text': 'y'}]}, Fake())
    assert result['claims'][0]['status'] == 'unknown'


def test_video_catches_event_between_uniform_frames():
    report = video({})
    assert not any(13 <= i <= 15 for i in report['uniform_frames'])
    assert 13 in report['extra_frames']
    assert len(report['extra_frames']) <= 8
    assert select([0, .5, .8], 10, 1)[1] == [2]


def test_video_invalid_file():
    with pytest.raises(ValueError):
        video({'video': 'nonexistent-video.mp4'})


def test_real_video_decode_and_live_caption_adapter(tmp_path):
    import cv2
    import numpy as np
    path = str(tmp_path / 'event.avi')
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'MJPG'), 10, (64, 64))
    assert writer.isOpened()
    for i in range(30):
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        if 13 <= i <= 15:
            frame[16:48, 16:48] = 255
        writer.write(frame)
    writer.release()
    class FakeVision:
        def complete(self, prompt, image=None):
            assert image.startswith('data:image/jpeg;base64,')
            return 'test caption', 10
    result = video({'video': path}, FakeVision())
    assert result['frames_scanned'] == 30
    assert 13 in result['extra_frames']
    assert len(result['descriptions']) == result['selected_count']


def test_budget_verifies_and_stops():
    result = reason({'a': 10, 'b': 5, 'candidate_answers': ['14', '15', '16']})
    assert result['verified'] and result['calls'] == 2
    assert result['usage_tokens'] == 0


def test_budget_exhaustion_is_not_success():
    result = reason({'a': 10, 'b': 5, 'candidate_answers': ['wrong'], 'budget': {'calls': 1}})
    assert not result['verified'] and result['stop_reason'] == 'call_limit'
    assert reason({'a': 1, 'b': 2, 'budget': {'calls': 0}})['calls'] == 0


def test_budget_time_limit():
    ticks = iter([0, 31, 31])
    result = reason({'a': 1, 'b': 2}, clock=lambda: next(ticks))
    assert result['stop_reason'] == 'time_limit' and result['calls'] == 0


@pytest.mark.parametrize('poc', ['06', '07', '08', '09', '10', '11'])
def test_cli_demo(poc, tmp_path):
    output = tmp_path / 'report.json'
    result = subprocess.run([sys.executable, '-m', 'poc_lab', poc, '--output', str(output)],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())['poc'] == poc
