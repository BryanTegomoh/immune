import React,{useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {request,exportJSON} from './api';
import {Ledger,Results,Setup} from './components';
import {OwnerAccess} from './OwnerAccess';
import './style.css';

function App(){
 const [state,setState]=useState(null),[selected,setSelected]=useState('T01'),[label,setLabel]=useState('REVISE'),[rationale,setRationale]=useState('');
 const [error,setError]=useState(''),[notice,setNotice]=useState(''),[sending,setSending]=useState(false),[pendingUntil,setPendingUntil]=useState(0);
 const [confirmTrain,setConfirmTrain]=useState(false);
 const [dark,setDark]=useState(()=>window.matchMedia('(prefers-color-scheme: dark)').matches);
 useEffect(()=>{document.documentElement.dataset.theme=dark?'dark':'light'},[dark]);
 const refresh=async()=>{try{setState(await request('state'));}catch(e){setError(e.message)}};
 useEffect(()=>{refresh();const interval=setInterval(refresh,15000);return()=>clearInterval(interval)},[]);
 const current=state?.cases.find(c=>c.id===selected), count=state?Object.keys(state.corrections).length:0;
 useEffect(()=>{if(current){const saved=state.corrections[current.id];setLabel(saved?.label||current.label);setRationale(saved?.rationale||current.rationale);}},[selected,!!state]);
 async function act(action){
  if(action==='train'&&!confirmTrain){setConfirmTrain(true);return;}
  setConfirmTrain(false);setError('');setNotice('');setSending(true);
  try{
   const result=await request('action',{action,confirm_training:action==='train'});
   if(state.hosted){setPendingUntil(Date.now()+25000);setNotice(result.message);}
   await refresh();
  }catch(e){setError(e.message)}finally{setSending(false)}
 }
 async function save(){
  setError('');setSending(true);
  try{
   const result=await request('correct',{case_id:selected,label,rationale});
   if(state.hosted){setPendingUntil(Date.now()+25000);setNotice(`${selected}: save job accepted. Wait for the job to finish before starting another operation.`)}
   else setNotice(`${selected}: expert correction saved locally. Sync to record it in GBrain.`);
   await refresh();
  }catch(e){setError(e.message)}finally{setSending(false)}
 }
 if(!state)return <main><h1>IMMUNE</h1><p role="status">{error||'Opening the workbench…'}</p></main>;
 const locked=state.hosted&&!state.authenticated;
 const busy=state.busy||sending||Date.now()<pendingUntil;
 const run=state.runs.at(-1), step=run?.trained?3:state.job?.action==='train'&&state.busy?2:count?1:0;
 return <>
  <a className="skip-link" href="#main">Skip to content</a>
  <header>
   <a className="brand" href="/" aria-label="IMMUNE home"><svg width="28" height="32" viewBox="0 0 28 32" fill="none" aria-hidden="true"><path d="M14 2L25 6v9c0 7-5 12-11 15C8 27 3 22 3 15V6L14 2Z" stroke="currentColor" strokeWidth="2"/><path d="M8 16l4 4 8-9" stroke="currentColor" strokeWidth="2"/></svg>IMMUNE</a>
   <span className="tagline">An immune system for AI agents.</span>
   <span className="mode">{state.hosted?(locked?'Recorded evidence':'Owner workspace'):state.configured.River?'River configured':'Local rehearsal'}</span>
   <button className="theme-toggle" aria-label={dark?'Switch to light mode':'Switch to dark mode'} onClick={()=>setDark(!dark)}>{dark?'Light':'Dark'}</button>
  </header>
  <main id="main">
   <section className="hero"><div><h1>Turn a failure into a lesson.</h1><p>Correct. Remember. Train. Test on unseen cases.</p></div>
    <div className="main-actions"><button className="primary" disabled={busy||!state.configured.River} onClick={()=>act('baseline')}>Run baseline</button><button disabled={busy||!state.configured.River||!count} onClick={()=>act('train')}>Train &amp; verify</button></div>
   </section>
   <OwnerAccess state={state} refresh={refresh}/>
   {confirmTrain&&<section className="train-confirm" role="alert"><h2>Confirm a paid training run</h2><p>Train on the {count} saved expert corrections and evaluate the 12 fixed held-out cases. This consumes River credits. Unsaved edits are not included. Results may improve, regress, or remain unchanged.</p><button className="primary" disabled={busy} onClick={()=>act('train')}>Approve and run training</button><button onClick={()=>setConfirmTrain(false)}>Cancel</button></section>}
   <nav className="stepper" aria-label="Learning workflow">{['Evaluate','Correct','Learn','Verify'].map((name,i)=><div className={i===step?'active':''} key={name}><span>{'0'+(i+1)}</span><b>{name}</b></div>)}</nav>
   {(error||state.job?.status==='error')&&<div role="alert" className="alert">{error||state.job.error}</div>}
   {state.busy&&<div role="status" className="progress"><span className="pulse"/>{state.job?.stage}<span>Live operation</span></div>}
   {notice&&<p role="status" className="notice">{notice}</p>}
   <section className="workbench">
    <section className="review">
     <div className="section-top"><h2 className="eyebrow">Case review</h2><span className="caption">{count}/24 approved</span></div>
     <label className="sr-only" htmlFor="case">Training case</label>
     <select id="case" value={selected} disabled={busy} onChange={e=>{setSelected(e.target.value);setNotice('')}}>{state.cases.filter(c=>c.split==='train').map(c=><option key={c.id} value={c.id}>{c.id} · {c.title}{state.corrections[c.id]?' · Reviewed':''}</option>)}</select>
     <div className="evidence"><h3>Supplied context</h3><p>{current.context}</p></div>
     <div className="evidence"><h3>Agent output</h3><p>{current.output}</p></div>
     <div className="decisions" role="group" aria-label="Expert decision">{['SHIP','REVISE','ESCALATE'].map(x=><button key={x} disabled={busy||locked} aria-pressed={label===x} className={label===x?'selected':''} onClick={()=>setLabel(x)}>{x}</button>)}</div>
     <label className="eyebrow rationale-label" htmlFor="rationale">Expert rationale</label>
     <textarea id="rationale" disabled={busy||locked} value={rationale} maxLength={4000} onChange={e=>setRationale(e.target.value)}/>
     <div className="save-row"><button className="primary" disabled={busy||locked||!rationale.trim()} onClick={save}>Save expert correction</button><button disabled={busy} onClick={()=>{const rows=state.cases.filter(c=>c.split==='train');setSelected(rows[(rows.findIndex(c=>c.id===selected)+1)%rows.length].id);setNotice('')}}>Next case</button></div>
     <p className="caption">{locked?'Unlock Owner access to save corrections and run experiments. Public visitors can inspect the recorded evidence.':'Review before saving. Only approved synthetic examples enter training. No patient data.'}</p>
    </section>
    <Ledger state={{...state,busy}} act={act}/>
   </section>
   <Results state={state}/>
   <div className="bottom-tools">{state.hosted?<p className="caption">Provider secrets stay in GitHub Actions. QM, Superset and UFO are not connected to this deployment.</p>:<Setup/>}<button onClick={()=>exportJSON(state)}>Export experiment</button></div>
   {state.events.length>0&&<details className="activity"><summary>Activity · {state.events.length} events</summary><ol>{state.events.slice().reverse().map((e,i)=><li key={i}><time>{new Date(e.at*1000).toLocaleTimeString()}</time>{e.text}</li>)}</ol></details>}
   <footer><span>Synthetic cases. No clinical validation.</span><span>IMMUNE · Own Your Intelligence · 2026</span></footer>
  </main>
 </>;
}
createRoot(document.getElementById('root')).render(<App/>);
