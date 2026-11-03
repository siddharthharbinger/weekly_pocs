"""Cheap full-frame scan chooses extra frames for expensive vision inference."""
import base64
import cv2
import numpy as np


def select(scores, stride=10, budget=8, threshold=.02):
    if stride < 1 or budget < 0 or not 0 <= threshold <= 1:
        raise ValueError('Invalid sampling parameters.')
    uniform = list(range(0, len(scores), stride))
    candidates = [i for i, score in enumerate(scores) if score >= threshold and i not in uniform]
    extra = sorted(candidates, key=lambda i: (-scores[i], i))[:budget]
    return uniform, sorted(extra)


def run(data, llm=None):
    capture = None
    if data.get('video'):
        capture = cv2.VideoCapture(data['video'])
        if not capture.isOpened():
            capture.release()
            raise ValueError('Cannot open video.')
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not fps or not np.isfinite(fps) or fps <= 0:
            capture.release()
            raise ValueError('Video has no valid frame rate.')
        def frames():
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                yield frame
    else:
        fps = 10
        def frames():
            for i in range(30):
                frame = np.zeros((64, 64, 3), dtype=np.uint8)
                if 13 <= i <= 15:
                    frame[16:48, 16:48] = 255
                yield frame
    previous, scores = None, []
    try:
        for frame in frames():
            gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (64, 64)).astype(float)
            scores.append(float(np.mean(np.abs(gray-previous))/255) if previous is not None else 0)
            previous = gray
    finally:
        if capture:
            capture.release()
    if not scores:
        raise ValueError('No decodable frames.')
    uniform, extra = select(scores, data.get('stride', 10), data.get('budget', 8), data.get('threshold', .02))
    report = {'frames_scanned': len(scores), 'uniform_frames': uniform, 'extra_frames': extra,
              'extra_timestamps': [i/fps for i in extra], 'selected_count': len(uniform)+len(extra)}
    if llm:
        descriptions = []
        if data.get('video'):
            capture = cv2.VideoCapture(data['video'])
        try:
            for index, frame in enumerate(frames()):
                if index in set(uniform + extra):
                    ok, encoded = cv2.imencode('.jpg', cv2.resize(frame, (512, 512)))
                    if not ok:
                        raise ValueError('Frame encoding failed.')
                    uri = 'data:image/jpeg;base64,' + base64.b64encode(encoded).decode()
                    text, _ = llm.complete('Describe visible objects and their positions.', image=uri)
                    descriptions.append({'frame': index, 'description': text})
        finally:
            if capture:
                capture.release()
        report['descriptions'] = descriptions
    return report
