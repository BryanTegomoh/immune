"""Manual GitHub Actions runner. Secrets are consumed only as environment variables."""
import json
import os
import time
from contextlib import closing
from . import engine,providers

def wait_for(action):
    engine.start(action)
    last=None
    while engine.BUSY:
        job=engine.snapshot()['job']
        if job['stage']!=last:
            print(job['stage'],flush=True); last=job['stage']
        time.sleep(.5)
    job=engine.snapshot()['job']
    if job['status']!='complete': raise RuntimeError(job.get('error','Operation failed.'))

def approved_ids(raw,confirmed):
    if confirmed!='true': raise ValueError('Training requires confirmation of your review.')
    ids=[x.strip() for x in raw.split(',') if x.strip()]
    allowed={c['id'] for c in engine.DATA if c['split']=='train'}
    if not ids or len(ids)!=len(set(ids)) or not set(ids)<=allowed:
        raise ValueError('Provide distinct reviewed training IDs such as T01,T02,T03. Held-out IDs are prohibited.')
    return ids

def main():
    op=os.getenv('IMMUNE_OPERATION','check-connections')
    if op=='check-connections':
        import river_client as river
        results={}
        if not os.getenv('RIVER_API_KEY') or not os.getenv('GBRAIN_TOKEN'):
            raise ValueError('Add both RIVER_API_KEY and GBRAIN_TOKEN as repository Actions secrets.')
        with closing(river.Client(api_key=os.environ['RIVER_API_KEY'],timeout=120)) as client:
            results['river_healthy']=client.health_check()
            results['river_models']=list(client.get_capabilities())
        results['gbrain_tools']=providers.gbrain('discover')
        # Discovery is read-only. Actual write and recall are performed during train.
        (engine.RUNS/'connection-check.json').write_text(json.dumps(results,indent=2))
        print('River health and GBrain tool discovery completed. See the private results artifact.')
    elif op=='baseline':
        wait_for('baseline')
    elif op=='train':
        ids=approved_ids(os.getenv('IMMUNE_REVIEWED_CASES',''),os.getenv('IMMUNE_CONFIRM_REVIEWED','false'))
        for c in engine.DATA:
            if c['id'] in ids: engine.correct(c['id'],c['label'],c['rationale'])
        wait_for('sync')
        wait_for('recall')
        wait_for('train')
        print('Paired experiment finished. Download the artifact to inspect actual results.')
    else: raise ValueError('Unsupported operation.')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        message=str(exc)
        for key in ('RIVER_API_KEY','GBRAIN_TOKEN','MEMORABLE_API_KEY'):
            value=os.getenv(key)
            if value:message=message.replace(value,'[redacted]')
        print('IMMUNE stopped:',message[:1500])
        raise SystemExit(1)
