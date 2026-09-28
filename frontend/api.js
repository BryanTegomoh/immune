let ownerToken='';
export function setOwnerToken(token){ownerToken=token;}
export async function request(path,body){
  const headers={'Content-Type':'application/json',...(ownerToken?{Authorization:'Bearer '+ownerToken}:{})};
  const response=await fetch((import.meta.env.VITE_API_BASE||'')+'/api/'+path,body?{method:'POST',headers,body:JSON.stringify(body)}:{headers});
  const value=await response.json(); if(!response.ok)throw new Error(value.error||'Request failed'); return value;
}
export function exportJSON(data){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='immune-experiment.json';a.click();URL.revokeObjectURL(url);}
