import argparse
import json
import time
from . import engine

def main():
    p=argparse.ArgumentParser(description='IMMUNE local experiment runner')
    p.add_argument('action',choices=['baseline','train','connect','sync','recall','status','models'])
    args=p.parse_args()
    if args.action=='status': print(json.dumps(engine.snapshot(),indent=2)); return
    if args.action=='models':
        import os
        import river_client as river
        from contextlib import closing
        with closing(river.Client(api_key=os.environ['RIVER_API_KEY'])) as c:
            print('Healthy:',c.health_check())
            print(json.dumps(c.get_capabilities(),default=str,indent=2))
        return
    engine.start(args.action)
    last=''
    while engine.BUSY:
        job=engine.snapshot()['job']
        if job['stage']!=last: print(job['stage'],flush=True); last=job['stage']
        time.sleep(.5)
    job=engine.snapshot()['job']
    print(json.dumps(job,indent=2))
    if job['status']=='error': raise SystemExit(1)
if __name__=='__main__': main()
