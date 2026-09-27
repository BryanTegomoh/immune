"""Manual GitHub Actions runner. Secrets are consumed only as environment variables."""
import json
import os
import time
import uuid
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
        for provider,key in [('river','RIVER_API_KEY'),('gbrain','GBRAIN_TOKEN')]:
            if not os.getenv(key):
                results[provider]={'status':'missing_secret','name':key}
                continue
            try:
                if provider=='river':
                    with closing(river.Client(api_key=os.environ[key],timeout=120)) as client:
                        healthy=client.health_check()
                        models=list(client.get_capabilities())
                    results[provider]={'status':'ok' if healthy else 'unhealthy','healthy':healthy,'models':models}
                else:
                    results[provider]={'status':'ok','tools':providers.gbrain('discover')}
            except Exception as exc:
                message=str(exc)
                for secret in ('RIVER_API_KEY','GBRAIN_TOKEN','MEMORABLE_API_KEY'):
                    value=os.getenv(secret)
                    if value: message=message.replace(value,'[redacted]')
                results[provider]={'status':'error','message':message[:1500]}
        # Discovery is read-only. Actual write and recall are performed during train.
        (engine.RUNS/'connection-check.json').write_text(json.dumps(results,indent=2))
        print(json.dumps(results,indent=2),flush=True)
        if any(value['status']!='ok' for value in results.values()):
            raise RuntimeError('Connection check incomplete. See each provider status and the private results artifact.')
        print('River health and GBrain tool discovery completed. See the private results artifact.')
    elif op=='memory-check':
        marker='immune-memory-check-'+uuid.uuid4().hex
        fact=marker+' is a synthetic IMMUNE connectivity test, not an expert-approved training correction.'
        result={'marker':marker,'fact':fact,'write':providers.gbrain('remember',fact)}
        (engine.RUNS/'memory-check.json').write_text(json.dumps(result,indent=2))
        result['recall']=providers.gbrain('recall',marker)
        result['exact_fact_retrieved']=fact in json.dumps(result['recall'])
        (engine.RUNS/'memory-check.json').write_text(json.dumps(result,indent=2))
        if not result['exact_fact_retrieved']:
            raise RuntimeError('GBrain accepted the write, but the exact diagnostic fact was not found in recall.')
        print('GBrain write and recall passed: the exact unique diagnostic fact was retrieved.',flush=True)
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
