"""Isolated Round 55 development server."""

from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import app
import round55_http

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HollowDeep Round 55 World Builder</title>
<style>
body{background:#111827;color:#e5e7eb;font:15px system-ui;
max-width:1100px;margin:auto;padding:24px}
h1{color:#fbbf24}
section{border:1px solid #374151;border-radius:10px;
padding:18px;margin:18px 0}
input,select,textarea,button{background:#1f2937;color:white;
border:1px solid #4b5563;border-radius:6px;padding:9px}
button{cursor:pointer;background:#374151;margin:5px}
textarea{width:98%;height:380px;font:13px monospace}
pre{white-space:pre-wrap;overflow-wrap:anywhere}
</style>
</head>
<body>
<h1>HollowDeep World Builder — Round 55</h1>
<p>Private development builder. Native ZIP exports only.
No production deployment.</p>

<section>
<h2>Create Area</h2>
<input id="a" type="number" value="14">
<input id="b" type="number" value="15">
<button onclick="createArea()">Create Area</button>
</section>

<section>
<h2>Add Room</h2>
<input id="room" type="number" value="16">
<button onclick="addRoom()">Add Native Room</button>
</section>

<section>
<h2>Connect Rooms</h2>
<input id="from" type="number" value="14">
<input id="to" type="number" value="15">
<select id="direction">
<option>north</option><option>south</option>
<option>east</option><option>west</option>
<option>up</option><option>down</option>
</select>
<button onclick="connectRooms()">Create Reciprocal Exit</button>
</section>

<section>
<h2>Area Editor</h2>
<p>Edit room names, descriptions, monsters and objects in the JSON.
Use the existing native catalog IDs.</p>
<textarea id="plan"></textarea>
<button onclick="exportArea()">Validate & Export ZIP</button>
</section>

<section>
<h2>Results</h2>
<pre id="status">Ready</pre>
<div id="download"></div>
</section>

<script>
const el=id=>document.getElementById(id);
const current=()=>JSON.parse(el("plan").value);

async function request(path,payload){
 const options=payload===undefined?{}:{
  method:"POST",
  headers:{"Content-Type":"application/json"},
  body:JSON.stringify(payload)
 };
 const r=await fetch(path,options);
 const data=await r.json();
 if(!r.ok)throw Error(data.error||"Request failed");
 return data;
}
function show(plan){
 el("plan").value=JSON.stringify(plan,null,2);
 el("status").textContent=
  "Area contains "+plan.rooms.length+" rooms";
}
async function execute(fn){
 try{await fn()}
 catch(e){el("status").textContent=e.message}
}
function createArea(){execute(async()=>{
 const a=Number(el("a").value),b=Number(el("b").value);
 show(await request("/api/new?a="+a+"&b="+b));
})}
function addRoom(){execute(async()=>{
 show(await request("/api/add-room",{
  plan:current(),room_id:Number(el("room").value)
 }));
})}
function connectRooms(){execute(async()=>{
 show(await request("/api/link",{
  plan:current(),
  a:Number(el("from").value),
  b:Number(el("to").value),
  direction:el("direction").value
 }));
})}
function exportArea(){execute(async()=>{
 const result=await request("/api/export",current());
 el("status").textContent=JSON.stringify(result,null,2);
 const link=document.createElement("a");
 link.href=result.download;
 link.textContent="Download native area ZIP";
 link.style.color="#fbbf24";
 el("download").replaceChildren(link);
})}
</script>
</body>
</html>"""


class Handler(round55_http.Handler):
    def do_GET(self):
        if urlsplit(self.path).path == "/":
            data = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8784), Handler)
    print("Round 55 listening on 127.0.0.1:8784", flush=True)
    server.serve_forever()
