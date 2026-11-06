'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, BookOpen, Check, ChevronRight, CircleHelp, Compass, Copy, DoorOpen, Flame, Maximize2, Minimize2, ScrollText, Send, Settings2, Shield, Sword, Swords, Terminal, Users, Volume2, VolumeX, X, Backpack, LogOut, Search, NotebookPen, EyeOff, RefreshCw, Code2, WandSparkles, Download } from 'lucide-react';
import { CommandPalette, AdventureJournal, NativeConnectionTools } from './components/ClientTools';
import { CommandWorkshop } from './components/CommandWorkshop';
import { createAnsiParser } from '../lib/ansi-parser.mjs';
import { validateCommand } from '../lib/client-utils.mjs';
import { getWorkshopProfile, resolveAlias } from '../lib/command-workshop.mjs';
import { transcriptText, searchTranscript } from '../lib/transcript.mjs';

type Session = { authenticated: boolean; configured: boolean; bridgeUrl?: string; ticket?: string | null; local?: boolean; native?: {host: string; port: number} | null };
type AnsiToken = { text: string; color?: string; bold?: boolean };
type Entry = { id: number; text: string; tokens?: AnsiToken[]; kind: 'system' | 'output' | 'input' | 'error' };
const COMMANDS = [
  { command: 'look', label: 'Look around', description: 'Read the room and discover its exits.', icon: Compass },
  { command: 'inventory', label: 'Inventory', description: 'See what you are carrying.', icon: Backpack },
  { command: 'score', label: 'Character', description: 'Review your character and progress.', icon: Shield },
  { command: 'who', label: 'Adventurers', description: 'Find other players in the realm.', icon: Users },
  { command: 'help', label: 'Game help', description: 'Read the original Mordor help files.', icon: BookOpen },
];

export default function Game() {
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<'offline' | 'connecting' | 'connected'>('offline');
  const [entries, setEntries] = useState<Entry[]>([]);
  const [input, setInput] = useState('');
  const [echo, setEcho] = useState(true);
  const [modal, setModal] = useState<'guide' | 'about' | 'settings' | 'login' | 'native' | 'commands' | 'journal' | 'workshop' | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [fontSize, setFontSize] = useState(13);
  const [muted, setMuted] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const [manualHidden, setManualHidden] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [realmHealth, setRealmHealth] = useState<{configured: boolean; online: boolean} | null>(null);
  const [checkingHealth, setCheckingHealth] = useState(false);
  const [logQuery, setLogQuery] = useState('');
  const [searchLog, setSearchLog] = useState(false);
  const socket = useRef<WebSocket | null>(null);
  const connecting = useRef(false);
  const echoEnabled = useRef(true);
  const modalRef = useRef<HTMLElement>(null);
  const outputRef = useRef<HTMLDivElement>(null);
  const terminalEnd = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const count = useRef(0);
  const ansi = useRef(createAnsiParser());
  const historyIndex = useRef(-1);
  const audio = useRef<{ context: AudioContext; gain: GainNode } | null>(null);
  const add = (text: string, kind: Entry['kind'] = 'system') => {
    const bounded = String(text).slice(-32000);
    const entry: Entry = { id: count.current++, text: bounded, kind, ...(kind === 'output' ? {tokens: ansi.current.push(bounded)} : {}) };
    setEntries(old => [...old, entry].slice(-400));
  };
  const hiddenInput = !echo || manualHidden;
  const transcript = useMemo(() => transcriptText(entries), [entries]);
  const logMatches = useMemo(() => searchTranscript(transcript, logQuery), [transcript, logQuery]);

  useEffect(() => {
    fetch('/api/session').then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(value => setSession(value as Session)).catch(() => setError('Could not check the realm connection. Try again in a moment.'));
    try { const size = Number(localStorage.getItem('hollowdeep-font')); if (size >= 11 && size <= 18) setFontSize(size); } catch {}
    const requested = new URLSearchParams(window.location.search).get('command');
    if (requested && validateCommand(requested).ok) {
      setInput(requested);
      const url = new URL(window.location.href); url.searchParams.delete('command');
      window.history.replaceState(null, '', url.pathname + url.search + url.hash);
    }
    checkHealth();
    return () => { socket.current?.close(); audio.current?.context.close(); };
  }, []);
  useEffect(() => { if (autoScroll && outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight; }, [entries, autoScroll]);
  useEffect(() => {
    if (!modal) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = modalRef.current;
    const focusable = () => Array.from(dialog?.querySelectorAll<HTMLElement>('button:not([disabled]),a[href],input,select,textarea,[tabindex="0"]') ?? []);
    focusable()[0]?.focus();
    const trap = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;
      const items = focusable(), first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener('keydown', trap);
    return () => { document.removeEventListener('keydown', trap); previous?.focus(); };
  }, [modal]);
  useEffect(() => {
    function key(event: KeyboardEvent) {
      if (event.key === 'Escape') { setModal(null); return; }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setModal('commands'); return; }
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement || modal || hiddenInput || event.ctrlKey || event.metaKey || event.altKey) return;
      if (status === 'connected' && event.key.toLowerCase() === 'i') { event.preventDefault(); send('inventory'); }
      if (status === 'connected' && event.key.toLowerCase() === 'c') { event.preventDefault(); send('score'); }
    }
    document.addEventListener('keydown', key);
    return () => document.removeEventListener('keydown', key);
  }, [status, modal, hiddenInput]);

  async function checkHealth() {
    setCheckingHealth(true);
    try { const response = await fetch('/api/status'); if (!response.ok) throw new Error(); setRealmHealth(await response.json()); }
    catch { setRealmHealth(null); }
    finally { setCheckingHealth(false); }
  }
  function compose(command: string) {
    if (!echoEnabled.current || manualHidden) { setError('Finish the hidden reply before preparing a command.'); return; }
    const valid = validateCommand(command);
    if (!valid.ok) { setError(valid.error ?? 'Invalid command.'); return; }
    setModal(null); setInput(command); setTimeout(() => inputRef.current?.focus(), 0);
  }

  async function connect() {
    if (status !== 'offline' || connecting.current) return;
    connecting.current = true;
    setError(''); setStatus('connecting');
    try {
      const response = await fetch('/api/session');
      if (!response.ok) throw new Error('The realm connection is temporarily unavailable.');
      const fresh: Session = await response.json(); setSession(fresh);
      if (!fresh.authenticated) { setStatus('offline'); connecting.current = false; setModal('login'); return; }
      if (!fresh.configured || !fresh.bridgeUrl) throw new Error('The original Mordor server is awaiting its persistent host. Your browser client is ready; the realm will open once the server is connected.');
      const target = new URL(fresh.bridgeUrl);
      if (fresh.ticket) target.searchParams.set('ticket', fresh.ticket);
      ansi.current.reset();
      const ws = new WebSocket(target); socket.current = ws;
      const timer = setTimeout(() => { ws.close(); setError('The realm did not respond. Please try again.'); setStatus('offline'); connecting.current = false; }, 15000);
      ws.onopen = () => { setEcho(true); echoEnabled.current = true; setInput(''); setManualHidden(false); };
      ws.onmessage = event => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'output') add(message.data ?? message.text ?? '', 'output');
          else if (message.type === 'echo') { const enabled = message.enabled !== false; echoEnabled.current = enabled; setEcho(enabled); setInput(''); }
          else if (message.type === 'error') { setError(message.message ?? message.text ?? 'The connection was interrupted.'); add(message.message ?? message.text ?? 'The connection was interrupted.', 'error'); }
          else if (message.type === 'status') {
            if (message.message) add(message.message);
            if (message.state === 'connected') { clearTimeout(timer); setStatus('connected'); connecting.current = false; setRealmHealth({configured: true, online: true}); inputRef.current?.focus(); }
          }
        } catch { add(String(event.data), 'output'); }
      };
      ws.onerror = () => setError('Unable to reach the game server. Check the server status and try again.');
      ws.onclose = () => { clearTimeout(timer); if (socket.current !== ws) return; setStatus('offline'); connecting.current = false; setEcho(true); echoEnabled.current = true; setInput(''); add('Disconnected from the realm. Reconnect to return to the original login prompt.'); };
    } catch (err) { setStatus('offline'); connecting.current = false; setError(err instanceof Error ? err.message : 'Connection unavailable.'); }
  }
  function send(command: string, allowHiddenReply = false) {
    if (socket.current?.readyState !== WebSocket.OPEN || status !== 'connected') { connect(); return; }
    if ((!echoEnabled.current || manualHidden) && !allowHiddenReply) { setError('Finish the hidden reply using the command line before using game shortcuts.'); return; }
    let storage: Storage | undefined;
    try { storage = window.localStorage; } catch {}
    const resolved = resolveAlias(command, getWorkshopProfile(storage), {hidden: !echoEnabled.current || manualHidden});
    if (!resolved.ok) { setError(resolved.error ?? 'Could not expand this alias.'); return; }
    const line = resolved.command;
    const valid = validateCommand(line);
    if (!valid.ok) { setError(valid.error ?? 'Enter one command, up to 256 bytes.'); return; }
    socket.current.send(JSON.stringify({ type: 'input', data: line }));
    if (echoEnabled.current && !manualHidden && line) { add(`› ${line}\n`, 'input'); setHistory(old => [line, ...old.filter(c => c !== line)].slice(0, 40)); }
    setInput(''); historyIndex.current = -1; inputRef.current?.focus();
  }
  function exportLog() {
    const text = ['HOLLOWDEEP — ADVENTURE LOG', new Date().toISOString(), '', transcript].join('\n');
    const url = URL.createObjectURL(new Blob([text], {type: 'text/plain;charset=utf-8'}));
    const link = document.createElement('a'); link.href = url; link.download = 'hollowdeep-adventure-log.txt';
    document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function toggleSound() {
    if (muted) {
      try {
        if (!audio.current) {
          const context = new AudioContext(); const gain = context.createGain(); gain.gain.value = 0.013; gain.connect(context.destination);
          [55, 82.4, 110.2].forEach(frequency => { const wave = context.createOscillator(); wave.type = 'sine'; wave.frequency.value = frequency; wave.connect(gain); wave.start(); });
          audio.current = { context, gain };
        }
        audio.current.context.resume(); setMuted(false);
      } catch { setError('Ambient audio is unavailable in this browser.'); }
    } else { audio.current?.context.suspend(); setMuted(true); }
  }
  const online = status === 'connected';
  const visibleEntries: Entry[] = logQuery.trim() ? logMatches.map((match: {line: number; text: string}) => ({id: match.line, text: match.text + '\n', kind: 'output'})) : entries;
  const actionLabel = status === 'connecting' ? 'Opening the gates…' : online ? 'Connected to Mordor' : session?.authenticated ? 'Enter the realm' : 'Sign in to enter';

  return <div className="app-shell">
    <header className="topbar">
      <a className="brand" href="/" aria-label="Hollowdeep home"><div className="brand-mark"><Flame size={26} strokeWidth={1.25} /></div><div>HOLLOWDEEP<small>A MORDOR 3.0 REALM</small></div></a>
      <nav className="top-nav" aria-label="Main navigation"><button className="active" onClick={() => setModal(null)}>Play</button><button onClick={() => setModal('native')}>MUD client</button><a href="/codex">Codex</a><a href="/guides">Guides</a><a href="/workshop">Build <ArrowRight size={13}/></a></nav>
      <div className="top-right"><span className="realm-version">ORIGINAL ENGINE · 3.00</span><button className="icon-button" aria-label="Settings" onClick={() => setModal('settings')}><Settings2 size={18}/></button></div>
    </header>

    <div className="game-layout">
      <aside className="left-sidebar">
        <div className="section-label">YOUR ADVENTURE</div>
        <div className="character-crest"><div className="crest-ring"><Shield size={39} strokeWidth={1}/><Sword className="crest-sword" size={31} strokeWidth={1}/></div><span className="crest-star">✦</span></div>
        <h2 className="character-name">An unwritten legend</h2><p className="character-description">Every adventurer starts<br/>with a name.</p>
        <button className="join-button" onClick={connect} disabled={status !== 'offline'}><DoorOpen size={15}/>{actionLabel}<ChevronRight size={14}/></button>
        <div className="sidebar-divider"/>
        <div className="section-label">EXPLORE</div>
        <button className="side-link selected" onClick={() => { setModal(null); inputRef.current?.focus(); }}><Compass size={18}/><span>The dungeon</span><span className="side-dot"/></button>
        <button className="side-link" disabled={!online} onClick={() => send('score')}><Shield size={18}/><span>Character</span><kbd>C</kbd></button>
        <button className="side-link" disabled={!online} onClick={() => send('inventory')}><Backpack size={18}/><span>Inventory</span><kbd>I</kbd></button>
        <button className="side-link" disabled={!online} onClick={() => send('who')}><Users size={18}/><span>Adventurers</span></button>
        <button className="side-link" onClick={() => setModal('commands')}><Search size={18}/><span>Command palette</span><kbd>⌘K</kbd></button>
        <button className="side-link" onClick={() => setModal('workshop')}><WandSparkles size={18}/><span>Command workshop</span></button>
        <button className="side-link" onClick={() => setModal('journal')}><NotebookPen size={18}/><span>Adventure journal</span></button>
        <a className="side-link" href="/codex"><ScrollText size={18}/><span>Realm codex</span></a>
        <a className="side-link" href="/workshop"><Code2 size={18}/><span>Server workshop</span></a>
        <div className="sidebar-note"><span>✧</span><p>Some stories are read.<br/><em>This one is yours to live.</em></p></div>
        <div className="sidebar-bottom"><button onClick={toggleSound}>{muted ? <VolumeX size={16}/> : <Volume2 size={16}/>}<span>Dungeon ambience</span><span className={'toggle ' + (!muted ? 'on' : '')}/></button><button onClick={() => setModal('guide')}><CircleHelp size={16}/>Need a hand?<ArrowUp size={12}/></button></div>
      </aside>

      <main className={'main-content ' + (expanded ? 'terminal-expanded' : '')}>
        <div className="breadcrumbs"><span>The realm</span><ChevronRight size={12}/><span>Mordor</span><ChevronRight size={12}/><strong>The beginning</strong></div>
        <div className="page-heading"><div><div className="eyebrow"><span/> THE NEXT CHAPTER IS YOURS</div><h1>Beyond the threshold.</h1></div><button className="share-button" onClick={async () => { try { await navigator.clipboard.writeText(window.location.origin); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { setError('Copy this page’s address to invite another adventurer.'); } }}>{copied ? <Check size={15}/> : <Copy size={15}/>}<span>{copied ? 'Link copied' : 'Invite a friend'}</span></button></div>

        <section className="scene" aria-label="Illustration of the dungeon entrance">
          <img src="/dungeon.png" alt="An ancient stone hall lit by amber braziers, with mist drifting through a distant arch"/>
          <div className="scene-shade"/><div className="scene-top"><span className="scene-tag"><Flame size={12}/> HOLLOWDEEP</span><span className="scene-tag subtle">A SHARED WORLD</span></div>
          <div className="scene-caption"><span className="scene-flourish">— ✦ —</span><h2>The gates are waiting.</h2><p>Old magic. Unfamiliar roads. A thousand stories yet to be told.</p></div>
          <span className="scene-bottom">EXPLORE · DISCOVER · BECOME</span>
        </section>

        <div className="realm-tool-cards" aria-label="Realm tools">
          <a href="/codex"><BookOpen size={19}/><span><strong>Learn your craft</strong><small>Classes, spells & commands</small></span><ArrowRight size={13}/></a>
          <button onClick={() => setModal('workshop')}><WandSparkles size={19}/><span><strong>Make it your own</strong><small>Aliases & command sequences</small></span><ArrowRight size={13}/></button>
          <a href="/workshop"><Code2 size={19}/><span><strong>Shape the realm</strong><small>Edit & export server code</small></span><ArrowRight size={13}/></a>
        </div>

        {realmHealth && !realmHealth.configured && <div className="realm-notice" role="status"><Flame size={15}/><span>The realm is awaiting its game host. Explore the command guide and journal while the gates are closed.</span></div>}
        <section className="terminal-panel" aria-label="Mordor game terminal">
          <div className="terminal-toolbar"><div className="terminal-title"><Terminal size={15}/><span>Adventure log</span><span className="small-tag">LIVE TERMINAL</span></div><div className="terminal-tools"><span className={'connection-state '+(online ? 'online' : '')}><i/>{online ? 'Connected' : status === 'connecting' ? 'Connecting' : 'Not connected'}</span><button className="icon-button" onClick={() => setExpanded(!expanded)} aria-label={expanded ? 'Restore terminal' : 'Expand terminal'}>{expanded ? <Minimize2 size={15}/> : <Maximize2 size={15}/>}</button></div></div>
          <div ref={outputRef} className="terminal-output" style={{ fontSize }} role="log" aria-live="polite" aria-label="Game output" onScroll={e => { const box = e.currentTarget; setAutoScroll(box.scrollHeight - box.scrollTop - box.clientHeight < 45); }}>
            {entries.length === 0 ? <div className="terminal-welcome"><div className="welcome-symbol">✧</div><div className="terminal-welcome-copy"><p className="welcome-heading">Welcome, traveler.</p><p>Your journey begins on the other side of the gate.</p><p>Connect to create a character or return to your adventure.</p><div className="welcome-tip"><span>TIP</span> New to MUDs? The codex will show you the way.</div></div></div> : visibleEntries.map(entry => <span key={entry.id} className={'terminal-entry '+entry.kind}>{entry.tokens ? entry.tokens.map((token, index) => <span key={index} style={{color: token.color, fontWeight: token.bold ? 600 : undefined}}>{token.text}</span>) : entry.text}{entry.kind !== 'output' && !entry.text.endsWith('\n') ? '\n' : ''}</span>)}
            {entries.length > 0 && visibleEntries.length === 0 && <p className="log-empty">No entries match your search.</p>}
            <div ref={terminalEnd}/>
          </div>
          {error && <div className="error-notice" role="alert"><CircleHelp size={16}/><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss message"><X size={14}/></button></div>}
          <div className="client-tool-strip"><button onClick={() => setModal('commands')}><Search size={12}/>Commands</button><button onClick={() => setModal('workshop')}><WandSparkles size={12}/>Aliases & macros</button><button onClick={() => setModal('journal')}><NotebookPen size={12}/>Journal</button><button aria-pressed={searchLog} onClick={() => { setSearchLog(!searchLog); setLogQuery(''); }}><Search size={12}/>Find in log</button><button disabled={!entries.length} onClick={exportLog}><Download size={12}/>Export log</button><button aria-pressed={hiddenInput} disabled={!echo} onClick={() => { setManualHidden(!manualHidden); setInput(''); }}><EyeOff size={12}/>{hiddenInput ? 'Input hidden' : 'Hide input'}</button>{!autoScroll && <button onClick={() => setAutoScroll(true)}><ArrowDown size={12}/>Latest</button>}</div>
          {searchLog && <label className="log-search"><Search size={14}/><input aria-label="Find in adventure log" value={logQuery} onChange={event => setLogQuery(event.target.value)} placeholder="Find a name, place, or message…" maxLength={100}/><span>{logQuery.trim() ? `${logMatches.length} matching lines` : 'Search this session'}</span></label>}
          <form className="command-line" onSubmit={e => { e.preventDefault(); send(input, true); }}><span className="prompt-mark">›</span><input ref={inputRef} aria-label={hiddenInput ? 'Mordor password' : 'Mordor command'} type={hiddenInput ? 'password' : 'text'} autoComplete="off" autoCapitalize="none" spellCheck={false} value={input} maxLength={256} onChange={e => setInput(e.target.value)} placeholder={online ? hiddenInput ? 'Hidden input — excluded from command history…' : 'What will you do? Enter a command…' : 'Enter the realm to begin your adventure…'} onKeyDown={e => { if (hiddenInput) return; if (e.key === 'ArrowUp' && history.length) { e.preventDefault(); historyIndex.current = Math.min(historyIndex.current + 1, history.length - 1); setInput(history[historyIndex.current]); } else if (e.key === 'ArrowDown') { e.preventDefault(); historyIndex.current = Math.max(historyIndex.current - 1, -1); setInput(historyIndex.current >= 0 ? history[historyIndex.current] : ''); } }}/><span className="enter-key">↵</span><button aria-label={online ? 'Send command' : 'Connect to realm'} disabled={status === 'connecting'}><Send size={17}/></button></form>
          <div className="terminal-footer"><span><span className="footer-dot"/> {online ? 'Original Mordor 3.0 server' : 'Your next adventure is one connection away'}</span><button disabled={!online} onClick={() => socket.current?.close()}><LogOut size={12}/>Disconnect</button></div>
        </section>
        <div className="under-terminal"><span><Shield size={13}/> Characters are saved by the original game engine.</span><span>Built for the journey.</span></div>
      </main>

      <aside className="right-sidebar">
        <section className="guide-card"><div className="card-heading"><Compass size={16}/><h2>Find your way</h2><span>01</span></div><p className="card-intro">A direction is the beginning<br/>of an adventure.</p><div className="compass-pad"><div className="compass-circle"/><span className="compass-n">N</span><button className="north" disabled={!online} onClick={() => send('north')} aria-label="Go north"><ArrowUp size={18}/></button><button className="west" disabled={!online} onClick={() => send('west')} aria-label="Go west"><ArrowLeft size={18}/></button><div className="compass-center"><Compass size={24} strokeWidth={1}/></div><button className="east" disabled={!online} onClick={() => send('east')} aria-label="Go east"><ArrowRight size={18}/></button><button className="south" disabled={!online} onClick={() => send('south')} aria-label="Go south"><ArrowDown size={18}/></button></div><div className="direction-tip">Or type <code>n</code> <code>s</code> <code>e</code> <code>w</code> to move.</div></section>
        <section className="guide-card quick-actions"><div className="card-heading"><BookOpen size={15}/><h2>At your command</h2></div><p className="card-intro">A few essentials for the road.</p>{COMMANDS.map(({command,label,icon:Icon}) => <button key={command} disabled={!online} onClick={() => send(command)}><Icon size={16}/><span>{label}</span><code>{command}</code></button>)}<button className="view-guide" onClick={() => setModal('guide')}>Open the field guide<ArrowRight size={14}/></button></section>
        <section className="realm-card"><div className="realm-card-symbol"><Swords size={25} strokeWidth={1}/></div><div className="eyebrow">BETTER TOGETHER</div><h3>No legend walks alone.</h3><p>Meet fellow travelers, share a tale, and face the unknown together.</p><div className="realm-card-bottom"><Users size={13}/><span>One world. Many stories.</span></div></section>
        <div className="right-footer">MORDOR 3.00 <span>✦</span> A CLASSIC, REAWAKENED</div>
      </aside>
    </div>

    {modal && <div className="modal-backdrop" onClick={() => setModal(null)}><section ref={modalRef} className={'modal ' + (modal === 'workshop' ? 'workshop-modal' : '')} role="dialog" aria-modal="true" aria-labelledby="modal-title" onClick={e => e.stopPropagation()}><button className="modal-close icon-button" aria-label="Close dialog" onClick={() => setModal(null)}><X size={20}/></button><div className="eyebrow">THE TRAVELER’S COMPANION</div><h2 id="modal-title">{modal === 'guide' ? 'Your field guide.' : modal === 'about' ? 'An old world. A new doorway.' : modal === 'login' ? 'Your story starts here.' : modal === 'native' ? 'Bring your favorite client.' : modal === 'commands' ? 'At your command.' : modal === 'journal' ? 'Remember the journey.' : modal === 'workshop' ? 'Your words. Your way.' : 'Make yourself at home.'}</h2>
      {modal === 'commands' && <CommandPalette onSelect={compose}/>}
      {modal === 'workshop' && <CommandWorkshop onPrepare={compose} hiddenInput={hiddenInput}/>}
      {modal === 'journal' && <AdventureJournal/>}
      {modal === 'native' && <><p>Connect directly with Mudlet, MUSHclient, or another telnet MUD client. The browser bridge connects to this same original Mordor world once its setup is complete.</p><div className="health-panel"><span className={'connection-state '+(realmHealth?.online ? 'online' : '')}><i/>{checkingHealth ? 'Checking browser bridge…' : !realmHealth ? 'Browser bridge status unavailable' : !realmHealth.configured ? 'Browser bridge setup pending' : realmHealth.online ? 'Browser bridge reachable' : 'Browser bridge unavailable'}</span><button className="secondary-button" disabled={checkingHealth} onClick={checkHealth}><RefreshCw size={13}/>Check again</button></div>{session?.native ? <><NativeConnectionTools host={session.native.host} port={session.native.port}/><p>The browser bridge status above does not test this direct Telnet endpoint. Create a new connection in your client, enter this hostname and port, then connect. Follow Mordor’s prompts to create or log into your character.</p><p className="fine-print">Native clients use your Mordor character password. ChatGPT sign-in is used only by this browser client. Telnet is unencrypted; use a password unique to this game.</p></> : <div className="native-pending"><Terminal size={22}/><h3>The public server address is not configured yet.</h3><p>Direct client connection details will appear here once the original Mordor server has a public TCP endpoint.</p></div>}</>}
      {modal === 'login' && <><p>Sign in with ChatGPT to enter the realm, then create or log into a character at the original Mordor prompt.</p><a className="join-button signin-link" href="/signin-with-chatgpt?return_to=%2F" target="_top"><DoorOpen size={16}/>Sign in with ChatGPT<ArrowRight size={16}/></a><p className="fine-print">Your character and game password are managed by the Mordor server.</p></>}
      {modal === 'guide' && <><p>Mordor is a shared, text-based roleplaying world. Read the game’s prompts, type your reply, and press Enter.</p><div className="guide-step"><span>01</span><div><h3>Enter the realm</h3><p>Sign in with ChatGPT, then connect. Follow Mordor’s original prompts to create or log into your character. Your game password is separate from your ChatGPT account.</p></div></div><div className="guide-step"><span>02</span><div><h3>Follow the story</h3><p>Room descriptions reveal exits, creatures, and objects. Try <code>look</code> first. Move with <code>north</code>, <code>south</code>, <code>east</code>, or <code>west</code>.</p></div></div><div className="command-grid">{COMMANDS.map(c => <div key={c.command}><code>{c.command}</code><p>{c.description}</p></div>)}<div><code>say hello</code><p>Speak to adventurers in your room.</p></div><div><code>kill &lt;creature&gt;</code><p>Begin combat with a named creature.</p></div><div><code>quit</code><p>Leave the world through the game.</p></div></div><p className="fine-print">Use the server’s <code>help</code> for the authoritative command list. The browser sends your commands directly to Mordor.</p></>}
      {modal === 'about' && <><p>Hollowdeep is a browser doorway into the original Mordor 3.00 multi-user dungeon by Brett Vickers and Brooke Paul.</p><div className="about-quote">“Some stories are read.<br/>This one is yours to live.”</div><p>The original server owns the world, character creation, combat, items, and saved characters. This client adds a modern interface, command shortcuts, and an accessible way to connect.</p><p className="fine-print">Mordor’s original copyright notices and distribution terms are preserved with the server source. The dungeon artwork was created for this browser client.</p><a className="text-link" href="https://godwars.net/~mudbytes/codebases.html" target="_blank" rel="noreferrer">Mordor source archive<ArrowRight size={14}/></a></>}
      {modal === 'settings' && <><p>A few small comforts for a long adventure.</p><label className="setting-row"><span>Terminal text size</span><select value={fontSize} onChange={e => { const size = Number(e.target.value); setFontSize(size); try { localStorage.setItem('hollowdeep-font', String(size)); } catch {} }}><option value={11}>Small</option><option value={13}>Default</option><option value={15}>Large</option><option value={18}>Extra large</option></select></label><div className="setting-row"><span>Dungeon ambience</span><button className="secondary-button" onClick={toggleSound}>{muted ? 'Turn on' : 'Turn off'}</button></div><p className="fine-print">Command history stays in this browser tab. Password replies are hidden and are never added to command history.</p>{session?.authenticated && !session.local && <a className="text-link" href="/signout-with-chatgpt?return_to=%2F" target="_top">Sign out of ChatGPT<LogOut size={14}/></a>}</>}
    </section></div>}
  </div>;
}
