"""Generate an offline Superset-ready evidence report from recorded state."""
import argparse, json, html
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('state')
p.add_argument('--memory')
p.add_argument('--output',default='docs/demo.html')
a=p.parse_args()
s=json.loads(Path(a.state).read_text()); run=s['runs'][-1]
m=json.loads(Path(a.memory).read_text()) if a.memory else {}
e=lambda x:html.escape(str(x))
cases={c['id']:c for c in json.loads(Path('data/cases.json').read_text())}
after={r['id']:r for r in run.get('trained',{}).get('rows',[])}
rows=[]
for r in run.get('baseline',{}).get('rows',[]):
 c=cases[r['id']]; t=after.get(r['id']); status='match' if r['predicted']==r['expected'] else 'miss'
 rows.append(f'<tr><td><details><summary>{e(r["id"])} · {e(r["title"])}</summary><p><b>Evidence:</b> {e(c["context"])}</p><p><b>Agent output:</b> {e(c["output"])}</p><p><b>Reference rationale:</b> {e(c["rationale"])}</p><p><b>Raw baseline:</b> {e(r["raw"])}</p></details></td><td>{e(r["expected"])}</td><td class="{status}">{e(r["predicted"])}</td><td>{e(t["predicted"]) if t else "Not run"}</td></tr>')
b=run.get('baseline',{}).get('metrics',{}); t=run.get('trained',{}).get('metrics',{})
draft=m.get('memorable',{}).get('draft',{}); judge=m.get('memorable',{}).get('judge',{})
steps=''.join('<li>'+e(x.get('action',''))+'</li>' for x in draft.get('steps',[]))
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>IMMUNE | Hackathon evidence</title><style>
*{box-sizing:border-box}body{margin:0;background:#fafbf8;color:#182019;font:16px/1.55 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:48px 24px}header{border-bottom:1px solid #d8dfd4;padding-bottom:30px}.eyebrow{font:12px ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase}h1{font-size:clamp(36px,6vw,68px);line-height:1.06;letter-spacing:-.05em;margin:22px 0}h2{font-size:23px}p{max-width:820px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0}.card{background:white;border:1px solid #d8dfd4;border-radius:14px;padding:22px}.number{font-size:36px;font-weight:700}.badge{display:inline-block;background:#dcf7a2;padding:4px 12px;border-radius:30px;font-size:13px}.muted{color:#596356}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:620px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #d8dfd4;padding:15px 10px}th{font-size:12px;text-transform:uppercase}.match{color:#286436}.miss{color:#ad4228}summary{cursor:pointer;font-weight:600}details p{font-size:14px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.6 ui-monospace,monospace;background:#f0f3eb;padding:18px;border-radius:10px}a{color:#315d20}section{margin-top:38px}footer{margin-top:40px;border-top:1px solid #d8dfd4;padding-top:20px;font-size:13px}@media(max-width:650px){.grid{grid-template-columns:1fr}main{padding:28px 16px}}
</style><main><header><div class="eyebrow">IMMUNE / Own Your Intelligence / September 27, 2026</div><h1>Make a correction.<br>Keep the lesson.</h1><p>A physician-built workbench connecting human review, persistent incident memory, procedure extraction, and measured model updates.</p><span class="badge">Recorded evidence, not simulated scores</span></header>'''
page+=f'<div class="grid"><div class="card"><div class="eyebrow">River baseline</div><div class="number">{b.get("correct",0)} / {b.get("n",0)}</div><p>Correct synthetic decisions. {b.get("invalid",0)} invalid outputs.</p></div><div class="card"><div class="eyebrow">After training</div><div class="number">{str(t.get("correct"))+" / "+str(t.get("n")) if t else "Not run"}</div><p>Human review is required before training.</p></div><div class="card"><div class="eyebrow">GBrain</div><div class="number">{"Retrieved" if m.get("exact_fact_retrieved") else "Pending"}</div><p>Unique diagnostic fact written and recalled. This was not an expert correction.</p></div></div>'
page+='<section><h2>Inspect every decision</h2><p class="muted">Expand a case to read the evidence and original output. Reference labels are synthetic drafts. This is not clinical validation.</p><div class="scroll"><table><thead><tr><th>Case and evidence</th><th>Reference</th><th>Baseline</th><th>Trained</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></section>'
page+='<section><h2>Memorable procedure extraction</h2><p>A real API response, retained as a draft in GBrain. Provider admission and storage are distinct.</p><ol>'+steps+'</ol><pre>'+e(json.dumps(judge,indent=2))+'</pre></section>'
page+='<section><h2>Provenance</h2><pre>'+e(json.dumps({k:run.get(k) for k in ['base_model','model_id','checkpoint','dataset_sha256','heldout_sha256','prompt_sha256','temperature','seed']},indent=2))+'</pre><p><a href="https://github.com/BryanTegomoh/immune/actions/runs/36358066104">River baseline run</a> · <a href="https://github.com/BryanTegomoh/immune/actions/runs/36359180942">GBrain and Memorable run</a></p></section><footer>Built from scratch during the hackathon. QM adapter and Superset launch configuration are prepared; activation in those products is not established by this report. UFO integration is not implemented. Training gains are not claimed.</footer></main></html>'
Path(a.output).write_text(page)
print(a.output)
