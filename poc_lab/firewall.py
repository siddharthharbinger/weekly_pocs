"""Deny-by-default gate for a deliberately small ticket-tool vocabulary."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Policy(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tools: list[Literal['read_ticket', 'update_ticket']]
    ticket_ids: list[str]
    max_calls: int = Field(default=5, ge=0)
    writable_fields: list[Literal['status', 'summary']] = []


class Action(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tool: str
    arguments: dict


class Firewall:
    def __init__(self, policy):
        self.policy = Policy.model_validate(policy)
        self.calls = 0

    def check(self, action):
        action = Action.model_validate(action)
        p, args = self.policy, action.arguments
        reason = None
        if action.tool not in p.tools:
            reason = 'tool not authorized'
        elif self.calls >= p.max_calls:
            reason = 'workflow call budget exhausted'
        elif args.get('ticket_id') not in p.ticket_ids:
            reason = 'ticket outside approved scope'
        elif action.tool == 'read_ticket' and set(args) != {'ticket_id'}:
            reason = 'unexpected read arguments'
        elif action.tool == 'update_ticket':
            fields = args.get('fields')
            if (set(args) != {'ticket_id', 'fields'} or not isinstance(fields, dict)
                    or not fields or not set(fields) <= set(p.writable_fields)
                    or not all(isinstance(v, str) for v in fields.values())):
                reason = 'write fields outside approved scope'
        if reason is None:
            self.calls += 1
        return {'decision': 'block' if reason else 'allow',
                'reason': reason or 'within approved scope', 'accepted_calls': self.calls}

    def dispatch(self, action, handlers):
        """Handlers can only run through an allow decision; no tool name eval."""
        result = self.check(action)
        if result['decision'] == 'allow':
            result['output'] = handlers[action['tool']](**action['arguments'])
        return result


def run(data):
    firewall = Firewall(data['policy'])
    return {'decisions': [firewall.check(a) for a in data['actions']]}
