import test from 'node:test';
import assert from 'node:assert/strict';
import handler,{validateCorrection} from '../api/workbench.js';

function response(){
 const r={statusCode:0,value:null,setHeader(){},status(n){this.statusCode=n;return this;},json(v){this.value=v;return this;}};
 return r;
}
test('anonymous public state is labeled and mutation is locked',async()=>{
 const r=response();
 await handler({method:'GET',query:{route:'state'},headers:{}},r);
 assert.equal(r.statusCode,200);assert.equal(r.value.authenticated,false);
 assert.equal(r.value.configured.River,false);
 assert.equal(r.value.runs.at(-1).baseline.metrics.correct,11);
 assert.equal(r.value.runs.at(-1).trained.metrics.correct,11);
 assert.equal(r.value.recall,null);
 const w=response();
 await handler({method:'POST',query:{route:'correct'},headers:{'content-type':'application/json'},body:{}},w);
 assert.equal(w.statusCode,401);
});
test('heldout and invalid corrections are rejected',()=>{
 assert.throws(()=>validateCorrection({case_id:'H01',label:'SHIP',rationale:'x'}));
 assert.throws(()=>validateCorrection({case_id:'T01',label:'PASS',rationale:'x'}));
 assert.throws(()=>validateCorrection({case_id:'T01',label:'SHIP',rationale:''}));
 assert.equal(validateCorrection({case_id:'T01',label:'REVISE',rationale:' Review '}).rationale,'Review');
});
test('cross-origin writes fail before authorization',async()=>{
 const r=response();
 await handler({method:'POST',query:{route:'auth'},headers:{'content-type':'application/json',origin:'https://attacker.example',host:'immune.vercel.app'},body:{}},r);
 assert.equal(r.statusCode,403);
});
test('unknown routes do not become successful jobs',async()=>{
 const r=response();
 await handler({method:'POST',query:{route:'nope'},headers:{},body:{}},r);
 assert.equal(r.statusCode,404);
});
test('owner can queue correction and training requires explicit consent',async()=>{
 const original=global.fetch;
 const calls=[];
 global.fetch=async(url,options)=>{
  calls.push({url,options});
  const value=url.endsWith('/user')?{login:'BryanTegomoh'}:
   url.endsWith('/repos/BryanTegomoh/immune')?{permissions:{push:true}}:
   url.includes('/runs?')?{workflow_runs:[]}:null;
  return new Response(value?JSON.stringify(value):null,{status:value?200:204});
 };
 try{
  const headers={'content-type':'application/json',authorization:'Bearer test-owner-only'};
  const r=response();
  await handler({method:'POST',query:{route:'correct'},headers,body:{case_id:'T01',label:'REVISE',rationale:'Synthetic review'}},r);
  assert.equal(r.statusCode,202);
  assert.equal(JSON.parse(calls.at(-1).options.body).inputs.action,'correct');
  const t=response();
  await handler({method:'POST',query:{route:'action'},headers,body:{action:'train'}},t);
  assert.equal(t.statusCode,400);
  const s=response();
  await handler({method:'GET',query:{route:'state'},headers},s);
  assert.equal(s.value.authenticated,true);
 }finally{global.fetch=original;}
});
test('other GitHub users cannot operate the app',async()=>{
 const original=global.fetch;
 global.fetch=async()=>new Response(JSON.stringify({login:'someone-else'}));
 try{
  const r=response();
  await handler({method:'POST',query:{route:'auth'},headers:{'content-type':'application/json',authorization:'Bearer another-test-token'},body:{}},r);
  assert.equal(r.statusCode,403);
 }finally{global.fetch=original;}
});
