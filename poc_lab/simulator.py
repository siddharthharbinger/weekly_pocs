"""Evaluate allowlisted actions against a disposable SQLite snapshot, never SQL/code."""
import sqlite3
from pydantic import BaseModel, ConfigDict, Field


class Change(BaseModel):
    model_config = ConfigDict(extra='forbid')
    account_id: int
    delta: int  # integer cents, avoiding floating-point money arithmetic


class Scenario(BaseModel):
    model_config = ConfigDict(extra='forbid')
    balances: dict[int, int]
    changes: list[Change]
    conserve_total: bool = True
    max_affected: int = Field(default=2, ge=0)


def run(data):
    scenario = Scenario.model_validate(data)
    source, sandbox = sqlite3.connect(':memory:'), sqlite3.connect(':memory:')
    try:
        source.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY, balance INTEGER)')
        source.executemany('INSERT INTO accounts VALUES (?, ?)', scenario.balances.items())
        source.commit()
        source.backup(sandbox)
        failures = []
        for change in scenario.changes:
            cursor = sandbox.execute('UPDATE accounts SET balance=balance+? WHERE id=?',
                                     (change.delta, change.account_id))
            if cursor.rowcount != 1:
                failures.append(f'unknown account {change.account_id}')
        after = dict(sandbox.execute('SELECT id,balance FROM accounts'))
        before = dict(source.execute('SELECT id,balance FROM accounts'))
        changed = [i for i in before if before[i] != after[i]]
        if any(v < 0 for v in after.values()):
            failures.append('negative balance')
        if scenario.conserve_total and sum(before.values()) != sum(after.values()):
            failures.append('total balance changed')
        if len(changed) > scenario.max_affected:
            failures.append('affected-record budget exceeded')
        return {'decision': 'review' if failures else 'allow', 'failures': failures,
                'before': before, 'simulated_after': after, 'affected': changed,
                'source_unchanged': before == scenario.balances}
    finally:
        sandbox.close()
        source.close()
