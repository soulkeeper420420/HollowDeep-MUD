import { env } from 'cloudflare:workers';

export async function GET(request: Request) {
  const runtime = env as unknown as Record<string, string | undefined>;
  const local = process.env.NODE_ENV === 'development' && ['localhost', '127.0.0.1', '[::1]'].includes(new URL(request.url).hostname);
  const headers = { 'Cache-Control': 'no-store' };
  if (!runtime.BRIDGE_URL && !local) return Response.json({ configured: false, online: false, checkedAt: Date.now() }, { headers });
  try {
    const target = new URL(local ? 'http://127.0.0.1:8788/health' : runtime.BRIDGE_URL!);
    if (!local && (target.protocol !== 'wss:' || target.username || target.password)) throw new Error('Invalid bridge address');
    target.protocol = local ? 'http:' : 'https:';
    target.pathname = '/health'; target.search = ''; target.hash = '';
    const response = await fetch(target, { signal: AbortSignal.timeout(4000), redirect: 'error' });
    const data = await response.json() as { ok?: boolean; engine?: boolean };
    return Response.json({ configured: true, online: response.ok && data.ok === true, checkedAt: Date.now() }, { headers });
  } catch {
    return Response.json({ configured: true, online: false, checkedAt: Date.now() }, { headers });
  }
}
