"""Persistent dependency-aware response cache with pluggable embeddings."""
import hashlib
import json
import math
import re
import sqlite3


def embed(text):
    """Dependency-free lexical baseline, not a learned semantic encoder."""
    words = re.findall(r'\w+', text.lower())
    return {w: words.count(w) for w in set(words)}


def cosine(a, b):
    norm = math.sqrt(sum(v*v for v in a.values()) * sum(v*v for v in b.values()))
    return sum(v*b.get(k, 0) for k, v in a.items()) / norm if norm else 0


class Cache:
    def __init__(self, path=':memory:', encoder=embed):
        self.db = sqlite3.connect(path)
        self.encoder = encoder
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY, digest TEXT);
            CREATE TABLE IF NOT EXISTS answers(question TEXT PRIMARY KEY, answer TEXT, vector TEXT, deps TEXT);
        ''')

    def close(self):
        self.db.close()

    def update_source(self, source_id, text):
        digest = hashlib.sha256(text.encode()).hexdigest()
        old = self.db.execute('SELECT digest FROM sources WHERE id=?', (source_id,)).fetchone()
        invalidated = []
        with self.db:
            if old and old[0] != digest:
                for q, deps in self.db.execute('SELECT question,deps FROM answers').fetchall():
                    if source_id in json.loads(deps):
                        invalidated.append(q)
                        self.db.execute('DELETE FROM answers WHERE question=?', (q,))
            self.db.execute('INSERT OR REPLACE INTO sources VALUES (?,?)', (source_id, digest))
        return invalidated

    def put(self, question, answer, dependencies):
        if not dependencies:
            raise ValueError('At least one explicit source dependency is required.')
        for dep in dependencies:
            if not self.db.execute('SELECT 1 FROM sources WHERE id=?', (dep,)).fetchone():
                raise ValueError(f'Unknown source: {dep}')
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO answers VALUES (?,?,?,?)',
                            (question, answer, json.dumps(self.encoder(question)), json.dumps(dependencies)))

    def get(self, question, threshold=0.75):
        if not 0 < threshold <= 1:
            raise ValueError('threshold must be in (0, 1]')
        vector = self.encoder(question)
        ranked = [(cosine(vector, json.loads(v)), q, a)
                  for q, a, v in self.db.execute('SELECT question,answer,vector FROM answers')]
        best = max(ranked, default=(0, None, None))
        return {'answer': best[2], 'matched_question': best[1], 'similarity': best[0]} if best[0] >= threshold else None


def run(data, path=':memory:'):
    cache = Cache(path)
    results = []
    try:
        for step in data['steps']:
            op = step['op']
            if op == 'source':
                results.append({'invalidated': cache.update_source(step['id'], step['text'])})
            elif op == 'put':
                cache.put(step['question'], step['answer'], step['dependencies'])
                results.append({'stored': True})
            elif op == 'get':
                results.append({'hit': cache.get(step['question'], step.get('threshold', .75))})
            else:
                raise ValueError(f'Unknown cache operation: {op}')
        return {'retrieval': 'lexical-cosine-baseline', 'results': results}
    finally:
        cache.close()
