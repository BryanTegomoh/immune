// Local verification server for the same handler deployed to Vercel.
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import handler from '../api/workbench.js';
const root=path.resolve('dist');
http.createServer(async(req,res)=>{
 const url=new URL(req.url,'http://localhost');
 if(url.pathname.startsWith('/api/')){
  req.query={route:url.pathname.slice(5)};
  let body='';for await(const chunk of req){body+=chunk;if(body.length>20000){res.writeHead(413);res.end();return;}}
  try{req.body=body?JSON.parse(body):{};}catch{res.writeHead(400);res.end('{"error":"Invalid JSON"}');return;}
  res.status=n=>{res.statusCode=n;return res;};
  res.json=v=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(v));return res;};
  return handler(req,res);
 }
 const file=path.resolve(root,'.'+(url.pathname==='/'?'/index.html':url.pathname));
 if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
 try{const bytes=await readFile(file);res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':'text/html');res.end(bytes);}
 catch{res.writeHead(404);res.end('Not found');}
}).listen(8770,'0.0.0.0',()=>console.log('Hosted workbench test server on 8770'));
