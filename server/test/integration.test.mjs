import test from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';
import http from 'node:http';
import { once } from 'node:events';
import { createHmac, randomUUID, generateKeyPairSync, webcrypto } from 'node:crypto';
import { mkdtemp, writeFile, symlink, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { WebSocket, WebSocketServer } from 'ws';
import { createBridge } from '../index.mjs';
import { createSessionTicket } from '../../lib/session-ticket.mjs';

const dependencies = { WebSocket, WebSocketServer };
const secret = 'test-only-bridge-key-with-at-least-32-bytes';
const origin = 'https://realm.example';
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(predicate, label = 'condition') {
  const end = Date.now() + 4000;
  while (!predicate()) {
    if (Date.now() > end) throw new Error(`Timed out waiting for ${label}`);
    await delay(5);
  }
}
const ticket = (sub = 'traveler', exp = Math.floor(Date.now()/1000)+60) => {
  const body = Buffer.from(JSON.stringify({sub, exp, nonce:randomUUID()})).toString('base64url');
  return body + '.' + createHmac('sha256', secret).update(body).digest('base64url');
};
async function fixture(t, config = {}, onConnect = () => {}) {
  const peers = [];
  const mud = net.createServer(socket => {
    socket.on('error', () => {});
    const peer = {socket, received:[], id:peers.length+1}; peers.push(peer);
    socket.on('data', chunk => peer.received.push(chunk));
    onConnect(peer);
  });
  mud.listen(0, '127.0.0.1'); await once(mud, 'listening');
  const bridge = await createBridge({port:0, host:'127.0.0.1', mordorPort:mud.address().port,
    secret, allowedOrigins:[origin], ...config}, dependencies);
  const address = await bridge.listen();
  const connections = [];
  t.after(async () => {
    for (const ws of connections) ws.terminate();
    await bridge.close();
    for (const peer of peers) peer.socket.destroy();
    await new Promise(resolve => mud.close(resolve));
  });
  function client(token = ticket(), requestedOrigin = origin, endpoint = '/socket') {
    const ws = new WebSocket(`ws://127.0.0.1:${address.port}${endpoint}${token === null ? '' : '?ticket='+token}`, {origin:requestedOrigin});
    const messages = [];
    ws.on('message', data => messages.push(JSON.parse(data)));
    ws.on('error', () => {});
    connections.push(ws);
    return {ws, messages};
  }
  return {bridge,mud,peers,client,base:`http://127.0.0.1:${address.port}`,port:address.port};
}
async function rejection(client) {
  return new Promise((resolve,reject) => {
    const timer = setTimeout(()=>reject(new Error('Expected WebSocket rejection')),4000);
    client.ws.once('unexpected-response', (_request,response) => { clearTimeout(timer); response.resume(); client.ws.terminate(); resolve(response.statusCode); });
    client.ws.once('open',()=>{clearTimeout(timer);reject(new Error('Unexpected accepted connection'));});
  });
}
async function connected(client) {
  await until(() => client.messages.some(m => m.type === 'status' && m.state === 'connected'), 'Mordor connection');
}

test('health checks the actual engine and reports failure when it is unreachable', async t => {
  const f = await fixture(t);
  const health = await fetch(f.base+'/health');
  assert.equal(health.status,200);
  assert.deepEqual(await health.json(),{ok:true,engine:true,service:'mordor-bridge'});
  const head = await fetch(f.base+'/health',{method:'HEAD'});
  assert.equal(head.status,200); assert.equal(await head.text(),'');
  for (const peer of f.peers) peer.socket.destroy();
  await new Promise(resolve => f.mud.close(resolve));
  await delay(1050);
  const failed = await fetch(f.base+'/health');
  assert.equal(failed.status,503);
  assert.equal((await failed.json()).ok,false);
});

test('independent browser sessions preserve their own commands and game output', async t => {
  const f = await fixture(t,{},peer => {
    peer.socket.write(`Welcome traveler ${peer.id}\r\n`);
    peer.socket.on('data', data => peer.socket.write(`Private ${peer.id}: ${data}`));
  });
  const a=f.client(ticket('first')), b=f.client(ticket('second'));
  await Promise.all([connected(a),connected(b)]);
  a.ws.send(JSON.stringify({type:'input',data:'say hello from first'}));
  b.ws.send(JSON.stringify({type:'input',data:'look'}));
  await until(()=>a.messages.some(m=>m.data?.includes('hello from first')) && b.messages.some(m=>m.data?.includes('look')));
  assert(!b.messages.some(m=>m.data?.includes('hello from first')));
  assert(!a.messages.some(m=>m.data?.includes('look')));
  assert(f.peers.some(p=>Buffer.concat(p.received).equals(Buffer.from('say hello from first\r\n'))));
  const states=a.messages.filter(m=>m.type==='status').map(m=>m.state);
  assert.deepEqual(states.slice(0,2),['connecting','connected']);
});

test('password echo negotiation is ordered, fragmented, and never echoed by the bridge', async t => {
  const f=await fixture(t);
  const client=f.client(); await connected(client);
  const peer=f.peers[0];
  peer.socket.write(Buffer.from([255]));
  await delay(10);
  peer.socket.write(Buffer.from([251,1]));
  peer.socket.write('Password: ');
  await until(()=>client.messages.some(m=>m.data==='Password: '));
  const hide=client.messages.findIndex(m=>m.type==='echo'&&!m.enabled);
  const prompt=client.messages.findIndex(m=>m.data==='Password: ');
  assert(hide>=0&&hide<prompt);
  client.ws.send(JSON.stringify({type:'input',data:'test-password-never-display'}));
  await until(()=>Buffer.concat(peer.received).includes(Buffer.from('test-password-never-display\r\n')));
  assert(!client.messages.some(m=>m.data?.includes('test-password-never-display')));
  peer.socket.write(Buffer.from([255,252,1]));
  await until(()=>client.messages.slice(prompt).some(m=>m.type==='echo'&&m.enabled));
});

test('origin, signed identity, expiry, and one-use session tickets are enforced', async t => {
  const f=await fixture(t);
  assert.equal(await rejection(f.client(ticket(),'https://other.example')),403);
  assert.equal(await rejection(f.client(null)),401);
  assert.equal(await rejection(f.client(ticket('late',Math.floor(Date.now()/1000)-1))),401);
  const single=ticket(); const a=f.client(single); await connected(a);
  assert.equal(await rejection(f.client(single)),401);
  assert.equal(await rejection(f.client(ticket(),origin,'/other')),404);
  a.ws.close(); await once(a.ws,'close');
  assert.equal(await rejection(f.client(single)),401);
});

test('Sites Ed25519 tickets reach the game once and reject legacy or foreign signatures', async t => {
  const keys = generateKeyPairSync('ed25519');
  const privateKeyPkcs8 = keys.privateKey.export({type:'pkcs8',format:'der'}).toString('base64');
  const publicKeySpki = keys.publicKey.export({type:'spki',format:'der'}).toString('base64');
  const f = await fixture(t, {secret:'', publicKeySpki}, peer => {
    peer.socket.on('data', data => peer.socket.write(data));
  });
  assert.equal(await rejection(f.client(ticket())), 401);
  const foreign = generateKeyPairSync('ed25519').privateKey.export({type:'pkcs8',format:'der'}).toString('base64');
  assert.equal(await rejection(f.client(await createSessionTicket({userId:'foreign',privateKeyPkcs8:foreign},webcrypto))), 401);
  const signed = await createSessionTicket({userId:'signed-player',privateKeyPkcs8},webcrypto);
  const player = f.client(signed);
  await connected(player);
  player.ws.send(JSON.stringify({type:'input',data:'look'}));
  await until(() => player.messages.some(message => message.data?.includes('look')));
  player.ws.close(); await once(player.ws,'close');
  assert.equal(await rejection(f.client(signed)), 401);
});

test('invalid, multiline, binary and oversized commands never reach the engine', async t => {
  const f=await fixture(t);
  const client=f.client(); await connected(client);
  const peer=f.peers[0];
  for(const value of ['north\nsouth','\x1b[31mlook','é'.repeat(129)]) client.ws.send(JSON.stringify({type:'input',data:value}));
  client.ws.send(Buffer.from('binary'));
  client.ws.send('{broken');
  await until(()=>client.messages.filter(m=>m.type==='error').length===5);
  assert.equal(Buffer.concat(peer.received).length,0);
  client.ws.send(JSON.stringify({type:'input',data:'look'}));
  await until(()=>Buffer.concat(peer.received).toString()==='look\r\n');
});

test('disconnect releases the per-user quota and terminates the corresponding TCP session', async t => {
  const f=await fixture(t);
  const a=f.client(),b=f.client(),c=f.client();
  await Promise.all([connected(a),connected(b),connected(c)]);
  assert.equal(await rejection(f.client()),429);
  a.ws.close(); await once(a.ws,'close');
  await until(()=>f.peers[0].socket.destroyed);
  const replacement=f.client(); await connected(replacement);
  const peer=f.peers.at(-1);
  peer.socket.end(); await once(replacement.ws,'close');
  assert(replacement.messages.some(m=>m.type==='status'&&m.state==='disconnected'));
});

test('failed TCP connections never emit a false connected state', async t => {
  const f=await fixture(t);
  await new Promise(resolve=>f.mud.close(resolve));
  const client=f.client(); await once(client.ws,'close');
  assert(client.messages.some(m=>m.type==='error'));
  assert(!client.messages.some(m=>m.type==='status'&&m.state==='connected'));
});

test('malformed upgrade requests do not consume a character session slot', async t => {
  const f=await fixture(t);
  const invalid=async()=>new Promise((resolve,reject)=>{
    const req=http.request(f.base+'/socket?ticket='+ticket(),{headers:{Origin:origin,Connection:'Upgrade',Upgrade:'websocket','Sec-WebSocket-Version':'13','Sec-WebSocket-Key':'invalid'}},res=>{res.resume();res.on('end',()=>resolve(res.statusCode));});
    req.on('error',reject); req.end();
  });
  for(let i=0;i<4;i++) assert.equal(await invalid(),400);
  const client=f.client(); await connected(client);
});

test('static serving blocks hidden files, malformed paths, and symlinks outside its root', async t => {
  const directory=await mkdtemp(path.join(os.tmpdir(),'mordor-static-'));
  t.after(()=>rm(directory,{recursive:true,force:true}));
  const publicDir=path.join(directory,'public');
  const {mkdir}=await import('node:fs/promises'); await mkdir(publicDir);
  await writeFile(path.join(publicDir,'index.html'),'<h1>Realm</h1>');
  await writeFile(path.join(publicDir,'.env'),'private');
  await writeFile(path.join(directory,'outside.txt'),'private');
  await symlink(path.join(directory,'outside.txt'),path.join(publicDir,'escape.txt'));
  const f=await fixture(t,{staticRoot:publicDir});
  assert.equal(await (await fetch(f.base+'/')).text(),'<h1>Realm</h1>');
  for(const name of ['/.env','/escape.txt','/%ZZ']) assert.equal((await fetch(f.base+name)).status,404);
  assert.equal((await fetch(f.base+'/',{method:'POST'})).status,405);
});

test('unsigned access is limited to explicit loopback development mode', async t => {
  const f=await fixture(t,{secret:'',allowLocal:true,allowedOrigins:[]});
  const local=f.client(null,'http://localhost:5173'); await connected(local);
  assert.equal(await rejection(f.client(null,'https://foreign.example')),403);
});
