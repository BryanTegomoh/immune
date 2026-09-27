"""Provider adapters. No simulated successes and no implicit fallback."""
import asyncio
import importlib.metadata
import json
import os
from contextlib import asynccontextmanager
from .core import POLICY, prompt, make_datum, parse_label, score, digest

@asynccontextmanager
async def gbrain_session():
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    token = os.getenv('GBRAIN_TOKEN')
    if not token:
        raise RuntimeError('Set GBRAIN_TOKEN in .env first.')
    async with streamablehttp_client('https://gbrain.io/mcp', headers={'Authorization': 'Bearer '+token}) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

def tool_args(schema, operation, content):
    from jsonschema import validate
    raw = os.getenv('GBRAIN_'+operation.upper()+'_ARGS')
    if raw:
        def expand(x):
            if isinstance(x, str): return x.replace('{content}', content).replace('{query}', content)
            if isinstance(x, dict): return {k: expand(v) for k,v in x.items()}
            if isinstance(x, list): return [expand(v) for v in x]
            return x
        args = expand(json.loads(raw))
    else:
        props = schema.get('properties', {})
        names = ('content','text','memory','note','body') if operation == 'remember' else ('query','text','question')
        name = next((k for k in names if k in props and props[k].get('type') == 'string'), None)
        if not name:
            raise RuntimeError('Unknown GBrain schema. Set GBRAIN_'+operation.upper()+'_ARGS from the discovered schema.')
        args = {name: content}
        defaults = {'title':'IMMUNE expert correction', 'tags':['immune','synthetic','expert-correction']}
        for key in schema.get('required', []):
            if key not in args and key in defaults: args[key] = defaults[key]
    validate(args, schema)
    return args

async def _gbrain(operation, content=None):
    async with gbrain_session() as session:
        result = await session.list_tools()
        available = [t for t in result.tools if t.name == operation or t.name.endswith('__'+operation) or t.name.endswith('_'+operation)]
        if operation == 'discover':
            return [{'name': t.name, 'inputSchema': t.inputSchema} for t in result.tools if any(x in t.name.lower() for x in ('remember','recall','search'))]
        if len(available) != 1:
            raise RuntimeError('Expected one '+operation+' tool; found '+str(len(available))+'. Check Full memory access in GBrain.')
        tool = available[0]
        result = await session.call_tool(tool.name, tool_args(tool.inputSchema, operation, content))
        if result.isError:
            raise RuntimeError('GBrain returned a tool error. Inspect the workspace Activity log.')
        return {'tool': tool.name, 'result': result.model_dump(mode='json')}

def gbrain(operation, content=None):
    return asyncio.run(_gbrain(operation, content))

def memorable(correction):
    import httpx
    key = os.getenv('MEMORABLE_API_KEY')
    if not key: raise RuntimeError('Set MEMORABLE_API_KEY in .env first.')
    payload = {'session_id': correction['event_id'], 'task_description':'Review a synthetic assistant output against evidence and human approval policy',
               'harness':'immune', 'tool_calls': correction['trace']}
    response = httpx.post('https://memorable-extraction-api.memorable.workers.dev/v1/extract',
        headers={'Authorization':'Bearer '+key}, json=payload, timeout=90)
    response.raise_for_status()
    value = response.json()
    if not isinstance(value.get('draft'), dict): raise RuntimeError('Memorable response has no procedure draft.')
    return value

def river_run(data, corrections, train, update):
    import river_client as river
    from transformers import AutoTokenizer
    from contextlib import closing
    key = os.getenv('RIVER_API_KEY')
    if not key: raise RuntimeError('Set RIVER_API_KEY in .env first.')
    base = os.getenv('RIVER_MODEL', 'Qwen/Qwen3.5-9B')
    held = [c for c in data if c['split'] == 'heldout']
    approved = [dict(c, label=corrections[c['id']]['label']) for c in data if c['split'] == 'train' and c['id'] in corrections]
    if train and not approved: raise ValueError('Approve at least one training correction first.')
    update('Loading tokenizer', {'base_model':base,'sdk_version':importlib.metadata.version('river-client')})
    tok = AutoTokenizer.from_pretrained(base)
    def render(c):
        return tok.apply_chat_template([{'role':'system','content':POLICY}, {'role':'user','content':prompt(c)}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)
    rendered = [render(c) for c in held]
    prompt_ids = [tok.encode(x, add_special_tokens=False) for x in rendered]
    def evaluate(model):
        groups = model.sample(prompt_token_ids=prompt_ids, num_samples=1, max_tokens=32, temperature=0.0, seed=27, timeout=600)
        if len(groups) != len(held): raise RuntimeError('Unexpected River sample count.')
        rows = [{'id':c['id'], 'title':c['title'], 'family':c['family'], 'expected':c['label'],
                 'predicted':parse_label(g[0].text), 'raw':g[0].text} for c,g in zip(held,groups)]
        return {'rows':rows, 'metrics':score(rows)}
    with closing(river.Client(api_key=key, timeout=600)) as client:
        with client.session(project='immune-hackathon', timeout=600) as session:
            model = session.create_model(base_model=base, lora=river.LoraConfig(rank=16, seed=27), tokenizer=tok, timeout=600)
            update('Measuring baseline', {'model_id':str(model.model_id), 'dataset_sha256':digest(data),
                'heldout_sha256':digest(held), 'training_sha256':digest(approved), 'approved_examples':len(approved),
                'temperature':0.0,'max_tokens':32,'seed':27,'lora_rank':16,'learning_rate':1e-4,'planned_steps':12,'prompt_sha256':digest(rendered)})
            before = evaluate(model)
            update('Baseline measured', {'baseline':before})
            if not train: return
            batch = [make_datum(tok,render(c),c['label']) for c in approved]
            losses = []
            for step in range(12):
                fb = model.forward_backward(batch, loss_fn='cross_entropy', timeout=600)
                model.optim_step(lr=1e-4, grad_clip_norm=1.0, timeout=600)
                losses.append(float(fb.metrics['loss']))
                update('Training '+str(step+1)+'/12', {'steps_completed':step+1,'losses':losses[:]})
            checkpoint = model.save_weights('immune-'+digest(approved)[:10], mode='inference', timeout=600)
            update('Testing unseen cases', {'checkpoint':str(checkpoint.path)})
            after = evaluate(model)
            update('Evaluation complete', {'trained':after})
