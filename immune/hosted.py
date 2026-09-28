"""Durable, serialized hosted operations; provider secrets stay in Actions."""
import json
import os
import time
from . import engine


def main():
    action = os.environ.get('IMMUNE_HOSTED_ACTION')
    if action not in ('correct', 'baseline', 'train', 'connect', 'sync', 'recall'):
        raise ValueError('Unknown hosted action.')
    if action == 'correct':
        correction = json.loads(os.environ.get('IMMUNE_HOSTED_CORRECTION', '{}'))
        engine.correct(correction.get('case_id'), correction.get('label'), correction.get('rationale'))
        engine.STATE['job'] = {'action': action, 'status': 'complete', 'stage': 'Correction saved'}
        engine.persist()
    else:
        if action == 'train' and os.environ.get('IMMUNE_CONFIRM_TRAINING') != 'true':
            raise ValueError('Training requires explicit confirmation.')
        engine.start(action)
        while engine.BUSY:
            time.sleep(.5)
        if engine.STATE['job']['status'] != 'complete':
            raise RuntimeError('Hosted operation failed. Inspect state.json for the redacted provider error.')
    print('Hosted operation complete; state is saved to the artifact.')


if __name__ == '__main__':
    main()
