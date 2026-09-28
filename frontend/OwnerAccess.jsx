import React,{useState} from 'react';
import {request,setOwnerToken} from './api';

export function OwnerAccess({state,refresh}){
 const [token,setToken]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 async function signIn(e){
  e.preventDefault();setError('');setBusy(true);setOwnerToken(token.trim());
  try{await request('auth',{});setToken('');await refresh();}
  catch(e){setOwnerToken('');setError(e.message);}
  finally{setBusy(false);}
 }
 if(!state.hosted)return null;
 return <section className="hosted-panel" aria-label="Hosted workbench">
  <div className="hosted-links"><strong>{state.authenticated?'Owner workspace':'Public evidence / owner-operated workbench'}</strong>
  <a href="https://github.com/BryanTegomoh/immune" target="_blank" rel="noreferrer">Source code</a>
  <a href="https://raw.githubusercontent.com/BryanTegomoh/immune/main/docs/IMMUNE-demo.mp4" target="_blank" rel="noreferrer">Watch recorded demo</a></div>
  <p>{state.evidence_note}</p>
  {state.hosted_run_url&&<p><a href={state.hosted_run_url} target="_blank" rel="noreferrer">View hosted job and logs</a></p>}
  {state.authenticated?<><p>{state.storage_note} New operations consume your provider credits when applicable.</p><button onClick={async()=>{setOwnerToken('');await refresh()}}>Lock owner access</button></>:
  <details><summary>Owner access: enable saving, training and memory operations</summary>
    <p>Only BryanTegomoh can operate this deployment. Authorize with a fine-grained GitHub token restricted to the IMMUNE repository: Actions read/write and Contents read. The token is held only in this tab's memory and sent over HTTPS to this app's backend and GitHub, never saved or logged. Reloading locks access.</p>
    <p>River, GBrain and Memorable keys remain in GitHub Actions secrets. Do not enter those keys here. This is a synthetic-case workbench; never enter patient data or private information.</p>
    <form onSubmit={signIn}><label htmlFor="owner-token">Repository-scoped GitHub token</label><input id="owner-token" type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)} required/><button type="submit" disabled={busy||!token.trim()}>{busy?'Checking access…':'Unlock owner workspace'}</button></form>
    {error&&<p role="alert">{error}</p>}
  </details>}
 </section>;
}
