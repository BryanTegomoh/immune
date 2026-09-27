export async function request(path,body){
  const response=await fetch('/api/'+path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
  const value=await response.json(); if(!response.ok)throw new Error(value.error||'Request failed'); return value;
}
export function exportJSON(data){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='immune-experiment.json';a.click();URL.revokeObjectURL(url);}
