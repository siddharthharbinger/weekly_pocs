"""Explicit, opt-in Groq access. Never log secrets or silently fall back."""
import json
import os
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv


class LLM:
    def __init__(self, env_file=None, model=None):
        load_dotenv(env_file or Path(__file__).resolve().parents[1] / '.env')
        if not os.getenv('GROQ_API_KEY'):
            raise ValueError('Set GROQ_API_KEY in .env or use --env-file.')
        self.model = model or os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')
        self.client = Groq(max_retries=0, timeout=30)

    def complete(self, prompt, max_tokens=512, timeout=30, image=None):
        content = prompt if image is None else [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': image}},
        ]
        response = self.client.chat.completions.create(
            model=self.model, messages=[{'role': 'user', 'content': content}],
            temperature=0, max_completion_tokens=max_tokens, timeout=timeout,
        )
        return response.choices[0].message.content or '', response.usage.total_tokens

    def structured(self, prompt, schema):
        text, _ = self.complete(prompt + '\nReturn only JSON matching this schema: '
                                + json.dumps(schema.model_json_schema()), 2048)
        return schema.model_validate_json(text)
