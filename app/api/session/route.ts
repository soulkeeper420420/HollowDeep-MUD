import { env } from 'cloudflare:workers';
import { createSessionTicket } from '../../../lib/session-ticket.mjs';

export async function GET(request: Request) {
  const runtime = env as unknown as Record<string, string | undefined>;
  const userId = request.headers.get('oai-authenticated-user-id');
  const url = new URL(request.url);
  const local = process.env.NODE_ENV === 'development' && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  const headers = { 'Cache-Control': 'no-store' };
  const nativePort = Number(runtime.MUD_PUBLIC_PORT);
  const native = runtime.MUD_PUBLIC_HOST && Number.isInteger(nativePort) && nativePort > 0 && nativePort <= 65535
    ? { host: runtime.MUD_PUBLIC_HOST, port: nativePort }
    : null;
  if (local) return Response.json({ authenticated: true, configured: true, local: true, native, bridgeUrl: 'ws://127.0.0.1:8788/socket', ticket: null }, { headers });
  const configured = !!runtime.BRIDGE_URL && !!(runtime.BRIDGE_SIGNING_KEY_PKCS8 || runtime.BRIDGE_SECRET);
  if (!userId) return Response.json({ authenticated: false, configured, native }, { headers });
  if (!configured) return Response.json({ authenticated: true, configured: false, native }, { headers });
  try {
    const target = new URL(runtime.BRIDGE_URL!);
    if (target.protocol !== 'wss:' || target.username || target.password || target.search || target.hash || target.pathname !== '/socket') throw new Error('Secure bridge configuration required');
    const ticket = await createSessionTicket({ userId, privateKeyPkcs8:runtime.BRIDGE_SIGNING_KEY_PKCS8, secret:runtime.BRIDGE_SECRET });
    return Response.json({ authenticated: true, configured: true, native, bridgeUrl: target.toString(), ticket }, { headers });
  } catch {
    return Response.json({ error: 'The realm connection is being configured.' }, { status: 503, headers });
  }
}
