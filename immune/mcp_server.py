"""Optional stdio tool surface for a harness such as QM. Uses the running app API."""
import json
import urllib.request
from mcp.server.fastmcp import FastMCP
mcp=FastMCP('immune', host='127.0.0.1', port=8767)
BASE='http://127.0.0.1:8765'

def request(path,payload=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=10) as r: return json.load(r)

@mcp.tool()
def evaluation_status() -> dict:
    """Read recorded experiment results. No fabricated scores or provider calls."""
    s=request('/api/state')
    return {k:s[k] for k in ('job','runs','configured','connections','dataset_sha256')}

@mcp.tool()
def approved_corrections() -> list:
    """Read human-approved training corrections only. Does not approve labels."""
    return list(request('/api/state')['corrections'].values())

@mcp.tool()
def run_immune(action: str) -> dict:
    """Run baseline, train, sync, or recall. Train uses River credits and only human-approved examples.
    The operator must request the operation. Poll evaluation_status for completion.
    """
    if action not in ('baseline','train','sync','recall'): raise ValueError('Unsupported operation')
    return request('/api/action',{'action':action})

if __name__=='__main__':
    import sys
    mcp.run(transport='streamable-http' if '--http' in sys.argv else 'stdio')
