import argparse
import json
import os
from pathlib import Path

FOLDERS = {
    '06': '06-permission-firewall', '07': '07-counterfactual-simulator',
    '08': '08-evidence-compiler', '09': '09-temporal-blindspot',
    '10': '10-semantic-cache', '11': '11-reasoning-budget',
}


def main(poc=None):
    parser = argparse.ArgumentParser(description='Weekly AI POCs: offline by default, JSON reports.')
    if poc is None:
        parser.add_argument('poc', choices=FOLDERS)
    parser.add_argument('--input', type=Path, help='Scenario JSON; defaults to bundled sample')
    parser.add_argument('--output', type=Path, help='Also save JSON report')
    parser.add_argument('--live', action='store_true', help='Opt into Groq calls (08, 09, 11)')
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--model')
    parser.add_argument('--db', default=':memory:', help='SQLite cache path (10 only)')
    args = parser.parse_args()
    poc = poc or args.poc
    path = args.input or Path(__file__).resolve().parents[1] / FOLDERS[poc] / 'sample.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        llm = None
        if args.live:
            if poc not in {'08', '09', '11'}:
                parser.error('--live is supported for 08, 09 and 11 only')
            from .llm import LLM
            if poc == '09' and not args.model:
                from dotenv import load_dotenv
                load_dotenv(args.env_file or Path(__file__).resolve().parents[1] / '.env')
                args.model = os.getenv('GROQ_VISION_MODEL')
                if not args.model:
                    raise ValueError('Set GROQ_VISION_MODEL or --model to a vision-capable model.')
            llm = LLM(args.env_file, args.model)
        if poc == '06':
            from .firewall import run
            result = run(data)
        elif poc == '07':
            from .simulator import run
            result = run(data)
        elif poc == '08':
            from .evidence import run
            result = run(data, llm)
        elif poc == '09':
            from .video import run
            result = run(data, llm)
        elif poc == '10':
            from .cache import run
            result = run(data, args.db)
        else:
            from .budget import run
            result = run(data, llm)
        output = json.dumps({'poc': poc, 'live': args.live, **result}, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output + '\n', encoding='utf-8')
        print(output)
    except Exception as exc:
        # SDK errors can contain request payloads; print type only for provider errors.
        if type(exc).__module__.startswith('groq'):
            parser.exit(1, f'Groq request failed ({type(exc).__name__}); check model access and credentials.\n')
        parser.exit(1, f'{type(exc).__name__}: {exc}\n')
