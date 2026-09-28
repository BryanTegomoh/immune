import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import evidence from './experiment.json';
import {Experiment, Review, About, Arrow} from './views';
import './style.css';

const pages=['Experiment','Try a review','About'];
function App(){
  const [page,setPage]=useState('Experiment');
  const {run}=evidence;
  return <><a className="skip" href="#content">Skip to content</a><header className="header"><a className="brand" href="#" onClick={()=>setPage('Experiment')} aria-label="IMMUNE home"><span className="brand-mark" aria-hidden="true"/>IMMUNE</a><nav aria-label="Main navigation">{pages.map(p=><button key={p} className={p===page?'current':''} aria-current={p===page?'page':undefined} onClick={()=>setPage(p)}>{p}</button>)}</nav><a className="source-link" href="/workbench/">Open workbench <Arrow/></a></header>
  <main id="content"><section className="hero"><h1>Expert judgment.<br/>Measurable learning.</h1><div className="hero-copy"><p>An expert corrects an agent. IMMUNE remembers the lesson, trains on approved decisions, and tests what changed.</p><span>Explore a completed River experiment, case by case.</span></div></section>
  <section className="metrics" aria-label="Recorded experiment results">{[[run.approved_examples,'Approved examples'],[run.steps_completed,'Training steps'],[`${run.baseline.metrics.correct}/12`,'Before training'],[`${run.trained.metrics.correct}/12`,'After training']].map(([value,label])=><div className="metric" key={label}><strong>{value}</strong><span>{label}</span></div>)}</section>
  <div className="page-content" key={page}>{page==='Experiment'?<Experiment evidence={evidence}/>:page==='Try a review'?<Review cases={evidence.cases.filter(c=>c.split==='train')}/>:<About evidence={evidence}/>}</div>
  </main><footer><span>Synthetic cases. No patient data. No clinical validation.</span><a href="https://github.com/BryanTegomoh" target="_blank" rel="noreferrer">Built by Bryan Tegomoh, MD, MPH <Arrow/></a></footer></>;
}
createRoot(document.getElementById('root')).render(<App/>);
