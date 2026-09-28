"""Operator CLI. Run --help; no paid provider calls without explicit opt-in."""
import argparse
import json
from pathlib import Path
import time
from .learning import Policy, Store, cycle, respond
from .river_learning import RiverLearning


def main():
    parser = argparse.ArgumentParser(description='IMMUNE bounded autonomous learning worker')
    parser.add_argument('--db', default='runs/autonomy.sqlite')
    parser.add_argument('--evaluation', required=True, help='Versioned target/retention/safety JSON suite')
    parser.add_argument('--policy', required=True, help='Bounded learning policy JSON')
    parser.add_argument('--model', default=None)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    ingest = commands.add_parser('ingest')
    ingest.add_argument('file')
    group = ingest.add_mutually_exclusive_group()
    group.add_argument('--human-approved', action='store_true', help='Operator attests to this correction, not to future updates')
    group.add_argument('--verifier', help='Registered verifier name; signed envelope required')
    run = commands.add_parser('run-once')
    run.add_argument('--allow-training', action='store_true')
    watch = commands.add_parser('watch')
    watch.add_argument('--allow-training', action='store_true', help='Authorize bounded unattended paid updates for this worker')
    watch.add_argument('--interval', type=int, default=60)
    commands.add_parser('rollback')
    commands.add_parser('recover', help='Acknowledge unknown/failed provider outcomes and clear a pause; never retries automatically')
    respond_cmd = commands.add_parser('respond')
    respond_cmd.add_argument('prompt_file')
    respond_cmd.add_argument('--allow-inference', action='store_true')
    args = parser.parse_args()
    policy = Policy(**json.loads(Path(args.policy).read_text()))
    evaluation = json.loads(Path(args.evaluation).read_text())
    provider = RiverLearning(args.model)
    store = Store(args.db, policy, evaluation, provider.identity)
    if args.command == 'status':
        result = store.status()
    elif args.command == 'ingest':
        value = json.loads(Path(args.file).read_text())
        if args.verifier:
            result = store.ingest(value['record'], verifier=args.verifier, signed=value.get('signature'))
        else:
            result = store.ingest(value, human=args.human_approved)
    elif args.command == 'run-once':
        result = cycle(store, provider, enabled=args.allow_training)
    elif args.command == 'watch':
        if not args.allow_training:
            parser.error('watch requires --allow-training; no paid loop was started.')
        if args.interval < 10:
            parser.error('Polling interval must be at least 10 seconds.')
        try:
            while True:
                print(json.dumps(cycle(store, provider, enabled=True)), flush=True)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            return
    elif args.command == 'rollback':
        result = store.rollback()
    elif args.command == 'recover':
        result = store.recover()
    else:
        if not args.allow_inference:
            parser.error('respond requires --allow-inference; it uses River credits.')
        result = respond(store, provider, Path(args.prompt_file).read_text())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
