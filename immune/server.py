"""Loopback-only demo server. No credentials sent to the browser."""
import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .core import ROOT
from . import engine

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass
    def reply(self, status, value):
        raw=json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/state': return self.reply(200,engine.snapshot())
        if path=='/api/export':
            value=engine.snapshot()
            return self.reply(200,value)
        if path.startswith('/api/'): return self.reply(404,{'error':'Not found'})
        base=(ROOT/'dist').resolve()
        target=(base/path.lstrip('/')).resolve() if path!='/' else base/'index.html'
        if not target.is_relative_to(base) or not target.is_file():
            return self.reply(404,{'error':'Build the frontend with npm run build first.'})
        raw=target.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type',mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers(); self.wfile.write(raw)
    def do_POST(self):
        origin=self.headers.get('Origin')
        if origin and origin not in ('http://127.0.0.1:'+str(self.server.server_port),'http://localhost:'+str(self.server.server_port),'http://127.0.0.1:5173','http://localhost:5173'):
            return self.reply(403,{'error':'Origin not allowed'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.reply(415,{'error':'JSON required'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<0 or size>20000: raise ValueError('Request too large')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict): raise ValueError('Object required')
            if self.path=='/api/correct': result=engine.correct(body.get('case_id'),body.get('label'),body.get('rationale'))
            elif self.path=='/api/action': result=engine.start(body.get('action'))
            else: return self.reply(404,{'error':'Not found'})
            return self.reply(200,result)
        except (ValueError,TypeError) as exc: return self.reply(400,{'error':str(exc)})
        except Exception: return self.reply(500,{'error':'Local server error. Check configuration.'})

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    print('IMMUNE: http://127.0.0.1:'+str(args.port),flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
if __name__=='__main__': main()
