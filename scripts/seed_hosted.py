"""Create a public synthetic snapshot without raw workspace memory or receipts."""
import json
import sys
from pathlib import Path

state = json.loads(Path(sys.argv[1]).read_text())
state.pop('recall', None)
state.pop('gbrain_tools', None)
state['recall'] = None
state['job'] = None
state['busy'] = False
state['events'] = []
state['connections'] = {'River': 'Recorded run verified', 'GBrain': 'Prior write/recall verified', 'Memorable': 'Drafts; quality gate failed'}
for correction in state.get('corrections', {}).values():
    correction.pop('gbrain_receipt', None)
state['procedures'] = {
    key: {'event_id': value.get('event_id'), 'response': {'judge': value.get('response', {}).get('judge', {}),
           'note': 'Public snapshot omits procedure content. Inspect the original run artifact for full evidence.'}}
    for key, value in state.get('procedures', {}).items()
}
Path('data/recorded-state.json').write_text(json.dumps(state, indent=2))
