import http from 'node:http';
import net from 'node:net';
import { readFile, realpath, stat } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { StringDecoder } from 'node:string_decoder';
import { randomUUID } from 'node:crypto';
import { TelnetDecoder, verifyTicket, validateInput, loadTicketPublicKey } from './protocol.mjs';

const isLoopback = ip => ['127.0.0.1', '::1', '::ffff:127.0.0.1'].includes(ip);
const localOrigin = value => {
  try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname); }
  catch { return false; }
};
const mime = { '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.css':'text/css; charset=utf-8', '.svg':'image/svg+xml', '.png':'image/png', '.webp':'image/webp', '.ico':'image/x-icon', '.woff2':'font/woff2' };

/** The CLI and integration tests use the same server. Dependencies are injectable for tests. */
export async function createBridge(config = {}, dependencies) {
  const { WebSocketServer, WebSocket } = dependencies || await import('ws');
  const port = Number(config.port ?? 8788);
  const host = config.host || '0.0.0.0';
  const mordorHost = config.mordorHost || '127.0.0.1';
  const mordorPort = Number(config.mordorPort ?? 4040);
  const secret = config.secret || '';
  const publicKey = config.publicKeySpki ? loadTicketPublicKey(config.publicKeySpki) : null;
  const allowLocal = config.allowLocal === true;
  const allowedOrigins = new Set(config.allowedOrigins || []);
  const staticRoot = config.staticRoot ? await realpath(config.staticRoot) : null;
  const encoding = config.encoding || 'latin1';
  const connectTimeout = config.connectTimeout ?? 10000;
  const healthTimeout = config.healthTimeout ?? 1500;
  const heartbeatMs = config.heartbeatMs ?? 30000;
  const idleMs = config.idleMs ?? 30 * 60000;
  if (secret && publicKey) throw new Error('Configure one ticket verification method: public key or legacy shared secret.');
  if (!secret && !publicKey && !allowLocal) throw new Error('BRIDGE_PUBLIC_KEY_SPKI or BRIDGE_SECRET is required. Local testing must explicitly set MORDOR_ALLOW_LOCAL=1.');
  if (secret && Buffer.byteLength(secret) < 32) throw new Error('BRIDGE_SECRET must contain at least 32 bytes.');
  if (!allowLocal && !allowedOrigins.size) throw new Error('ALLOWED_ORIGINS must include the public browser client origin.');
  if (!Number.isInteger(port) || port < 0 || port > 65535 || !Number.isInteger(mordorPort) || mordorPort < 1 || mordorPort > 65535) throw new Error('Invalid listening or MUD port.');
  if (!Buffer.isEncoding(encoding)) throw new Error('Unsupported MORDOR_ENCODING.');

  const usedTickets = new Map();
  const userConnections = new Map();
  const ipAttempts = new Map();
  const tcpSockets = new Set();
  let stopping = false;
  let healthFlight;
  let lastHealth;
  let lastHealthAt = 0;

  async function probeEngine() {
    if (stopping) return false;
    if (lastHealth !== undefined && Date.now() - lastHealthAt < 1000) return lastHealth;
    if (healthFlight) return healthFlight;
    healthFlight = new Promise(resolve => {
      const probe = net.createConnection({ host:mordorHost, port:mordorPort });
      tcpSockets.add(probe);
      let settled = false;
      const finish = online => {
        if (settled) return;
        settled = true;
        probe.destroy();
        tcpSockets.delete(probe);
        lastHealth = online;
        lastHealthAt = Date.now();
        resolve(online);
      };
      probe.setTimeout(healthTimeout);
      probe.once('connect', () => finish(true));
      probe.once('timeout', () => finish(false));
      probe.once('error', () => finish(false));
      probe.once('close', () => finish(false));
    }).finally(() => { healthFlight = null; });
    return healthFlight;
  }

  const server = http.createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'no-referrer');
    res.setHeader('Cache-Control', 'no-store');
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405).end(); return; }
    try {
      const url = new URL(req.url || '/', 'http://bridge.local');
      if (url.pathname === '/health') {
        const engine = await probeEngine();
        res.writeHead(engine ? 200 : 503, { 'Content-Type':'application/json' });
        res.end(req.method === 'HEAD' ? undefined : JSON.stringify({ ok:engine, engine, service:'mordor-bridge' }));
        return;
      }
      if (!staticRoot) { res.writeHead(url.pathname === '/' ? 200 : 404, { 'Content-Type':'text/plain; charset=utf-8' }).end(req.method === 'HEAD' ? undefined : url.pathname === '/' ? 'Hollowdeep Mordor bridge\n' : 'Not found\n'); return; }
      const relative = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
      if (relative.split('/').some(part => part.startsWith('.'))) throw new Error('Private path');
      const filename = await realpath(path.join(staticRoot, relative));
      if (!filename.startsWith(staticRoot + path.sep) || !(await stat(filename)).isFile()) throw new Error('Not a file');
      res.writeHead(200, {'Content-Type':mime[path.extname(filename)] || 'application/octet-stream'});
      res.end(req.method === 'HEAD' ? undefined : await readFile(filename));
    } catch { if (!res.headersSent) res.writeHead(404); res.end(); }
  });
  server.requestTimeout = 10000;
  server.headersTimeout = 10000;
  const wss = new WebSocketServer({ noServer:true, maxPayload:2048, perMessageDeflate:false });
  function reject(socket, status, message) {
    socket.end(`HTTP/1.1 ${status}\r\nConnection: close\r\nContent-Type: text/plain\r\nContent-Length: ${Buffer.byteLength(message)}\r\n\r\n${message}`);
  }
  server.on('upgrade', (req, socket, head) => {
    socket.on('error', () => {});
    try {
      if (stopping) return reject(socket, '503 Service Unavailable', 'The server is restarting');
      const url = new URL(req.url || '/', 'http://bridge.local');
      if (url.pathname !== '/socket') return reject(socket, '404 Not Found', 'Not found');
      const ip = req.socket.remoteAddress || '';
      const local = allowLocal && isLoopback(ip) && (!req.headers.origin || localOrigin(req.headers.origin));
      if (!local && (!req.headers.origin || !allowedOrigins.has(req.headers.origin))) return reject(socket, '403 Forbidden', 'Origin not allowed');
      const now = Date.now();
      const attempt = ipAttempts.get(ip);
      if (attempt && now - attempt.start < 60000 && attempt.count >= 30) return reject(socket, '429 Too Many Requests', 'Please wait before reconnecting');
      if (!attempt || now - attempt.start >= 60000) ipAttempts.set(ip, {start:now,count:1});
      else attempt.count++;
      let claims;
      const ticket = url.searchParams.get('ticket');
      if (ticket) claims = verifyTicket(ticket, publicKey || secret);
      else if (local) claims = {sub:`local:${ip}`,nonce:randomUUID(),exp:Math.floor(now/1000)+60};
      else return reject(socket, '401 Unauthorized', 'A signed session ticket is required');
      if (usedTickets.has(claims.nonce)) return reject(socket, '401 Unauthorized', 'Session ticket was already used');
      if ((userConnections.get(claims.sub) || 0) >= 3) return reject(socket, '429 Too Many Requests', 'Too many active sessions');
      if (wss.clients.size >= 200) return reject(socket, '503 Service Unavailable', 'The dungeon is full');
      // Commit quotas only after the WebSocket handshake has actually succeeded.
      wss.handleUpgrade(req, socket, head, ws => {
        usedTickets.set(claims.nonce, claims.exp * 1000);
        userConnections.set(claims.sub, (userConnections.get(claims.sub) || 0) + 1);
        wss.emit('connection', ws, claims);
      });
    } catch { reject(socket, '401 Unauthorized', 'Invalid or expired session ticket'); }
  });

  wss.on('connection', (ws, claims) => {
    let closed = false;
    let connected = false;
    let lastActivity = Date.now();
    let commandWindow = Date.now();
    let commandCount = 0;
    let alive = true;
    const decoder = new StringDecoder(encoding);
    const send = value => {
      if (ws.readyState !== WebSocket.OPEN) return;
      if (ws.bufferedAmount > 1024 * 1024) { ws.close(1013, 'Client too slow'); return; }
      ws.send(JSON.stringify(value));
    };
    const mud = net.createConnection({ host:mordorHost, port:mordorPort });
    tcpSockets.add(mud);
    mud.setNoDelay(true);
    mud.setTimeout(connectTimeout);
    const telnet = new TelnetDecoder({
      output:buffer => { const data = decoder.write(buffer); if (data) send({type:'output',data}); },
      reply:buffer => { if (!mud.destroyed) mud.write(buffer); },
      echo:enabled => send({type:'echo',enabled}),
    });
    send({type:'status',state:'connecting',message:'Connecting to the original Mordor server…'});
    send({type:'echo',enabled:true});
    mud.on('connect', () => { connected = true; mud.setTimeout(0); lastHealth = true; lastHealthAt = Date.now(); send({type:'status',state:'connected',message:'Connected to Mordor.'}); });
    mud.on('data', data => telnet.push(data));
    mud.on('timeout', () => { send({type:'error',message:'The Mordor server did not respond.'}); mud.destroy(); });
    mud.on('error', () => { lastHealth = false; lastHealthAt = Date.now(); send({type:'error',message:'The Mordor server is unavailable. Please reconnect shortly.'}); });
    mud.on('close', () => {
      tcpSockets.delete(mud);
      const tail = decoder.end();
      if (tail) send({type:'output',data:tail});
      send({type:'status',state:'disconnected',message:'The Mordor connection has closed.'});
      if (ws.readyState === WebSocket.OPEN) ws.close(1000, 'Mordor connection closed');
    });
    ws.on('pong', () => { alive = true; });
    ws.on('message', (raw, isBinary) => {
      if (isBinary) { send({type:'error',message:'Only text commands are supported.'}); return; }
      try {
        const input = validateInput(raw.toString('utf8'));
        const now = Date.now();
        if (now - commandWindow >= 1000) { commandWindow = now; commandCount = 0; }
        if (++commandCount > 10) { send({type:'error',message:'Slow down: at most 10 commands per second.'}); return; }
        if (!connected || mud.destroyed) { send({type:'error',message:'Wait for the Mordor connection before sending a command.'}); return; }
        if (mud.writableLength > 65536) { ws.close(1013, 'Server too slow'); return; }
        lastActivity = now;
        mud.write(input + '\r\n', 'utf8');
      } catch (error) { send({type:'error',message:error.message}); }
    });
    const heartbeat = setInterval(() => {
      if (!alive || Date.now() - lastActivity > idleMs) { ws.terminate(); mud.destroy(); return; }
      alive = false;
      ws.ping();
    }, heartbeatMs);
    const close = () => {
      if (closed) return;
      closed = true;
      clearInterval(heartbeat);
      mud.destroy();
      const count = (userConnections.get(claims.sub) || 1) - 1;
      if (count) userConnections.set(claims.sub, count); else userConnections.delete(claims.sub);
    };
    ws.on('error', close);
    ws.on('close', close);
  });
  const cleanup = setInterval(() => {
    const now = Date.now();
    for (const [nonce, expires] of usedTickets) if (expires <= now) usedTickets.delete(nonce);
    for (const [ip, value] of ipAttempts) if (now - value.start > 120000) ipAttempts.delete(ip);
  }, 60000);
  cleanup.unref();

  let stopPromise;
  return {
    server,
    wss,
    listen: () => new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(port, host, () => { server.off('error', reject); resolve(server.address()); });
    }),
    close: () => {
      if (stopPromise) return stopPromise;
      stopping = true;
      clearInterval(cleanup);
      stopPromise = new Promise(resolve => {
        for (const ws of wss.clients) ws.close(1001, 'Server restarting');
        for (const socket of tcpSockets) socket.destroy();
        const deadline = setTimeout(() => { for (const ws of wss.clients) ws.terminate(); server.closeAllConnections(); }, 250);
        server.close(() => { clearTimeout(deadline); wss.close(() => resolve()); });
      });
      return stopPromise;
    },
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const bridge = await createBridge({
    port:Number(process.env.PORT || 8788), host:process.env.HOST,
    mordorHost:process.env.MORDOR_HOST, mordorPort:Number(process.env.MORDOR_PORT || 4040),
    secret:process.env.BRIDGE_SECRET, publicKeySpki:process.env.BRIDGE_PUBLIC_KEY_SPKI,
    allowLocal:process.env.MORDOR_ALLOW_LOCAL === '1',
    allowedOrigins:(process.env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean),
    staticRoot:process.env.STATIC_DIR, encoding:process.env.MORDOR_ENCODING,
  });
  const address = await bridge.listen();
  console.log(`Mordor browser bridge listening on ${address.address}:${address.port}`);
  const stop = () => { bridge.close().then(() => process.exit(0)); };
  process.once('SIGTERM', stop);
  process.once('SIGINT', stop);
}
