'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, BookOpen, Check, ChevronRight, Compass, Copy, Flame, Search, Shield, Sparkles, Sword, Users, X } from 'lucide-react';
import { CHRONICLE_QUESTS, CODEX_CATEGORIES, CODEX_CLASS_COUNT, CODEX_ENTRIES, CODEX_SPELL_COUNT, commandHref, searchCodex } from '../../lib/realm-codex.mjs';
import './codex.css';

type Entry = { id: string; title: string; category: string; subtitle: string; tags: string[]; paragraphs: string[]; command: string; syntax: string; relatedCommands: string[]; source: string; extension?: boolean };
const entries = CODEX_ENTRIES as Entry[];
const icons: Record<string, typeof BookOpen> = { All: BookOpen, Classes: Shield, Spells: Sparkles, Combat: Sword, Social: Users, Progression: Flame, World: Compass, Chronicles: BookOpen, Staff: Shield };

export default function RealmCodex() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('All');
  const [selectedId, setSelectedId] = useState('class-fighter');
  const [copied, setCopied] = useState('');
  const [notice, setNotice] = useState('');
  const article = useRef<HTMLElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const results = searchCodex(query, category) as Entry[];
  const selected = results.find(entry => entry.id === selectedId) ?? results[0];

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get('topic');
    if (id && entries.some(entry => entry.id === id)) setSelectedId(id);
  }, []);

  function choose(entry: Entry) {
    setSelectedId(entry.id); setNotice(''); setCopied('');
    if (window.matchMedia('(max-width: 760px)').matches) {
      requestAnimationFrame(() => article.current?.scrollIntoView({ behavior: 'auto', block: 'start' }));
    }
  }
  function filter(next: string) { setCategory(next); setNotice(''); setCopied(''); }
  async function copy(command: string) {
    try { await navigator.clipboard.writeText(command); setCopied(command); setNotice('Command copied. Add a target where needed before sending it.'); }
    catch { setCopied(''); setNotice('Clipboard unavailable. Select the command above to copy it manually.'); }
  }
  const SelectedIcon = icons[selected?.category ?? 'All'];

  return <div className="codex-shell">
    <header className="codex-header"><a className="brand" href="/" aria-label="Hollowdeep home"><div className="brand-mark"><Flame size={26} strokeWidth={1.25}/></div><div>HOLLOWDEEP<small>THE REALM CODEX</small></div></a><nav aria-label="Codex navigation"><a href="/guides">Guides</a><a href="/workshop">Server workshop<ChevronRight size={13}/></a><a className="codex-return" href="/"><ArrowLeft size={14}/>Return to the dungeon</a></nav></header>
    <main className="codex-main">
      <div className="codex-intro"><div><span className="codex-eyebrow">KNOWLEDGE FOR THE ROAD</span><h1>Every legend starts<br/>with a little knowledge.</h1><p>Choose a calling. Learn the language of magic. Find the right words for your next adventure.</p></div><div className="codex-seal" aria-hidden="true"><div><BookOpen size={44} strokeWidth={1}/><span>THE REALM<br/>REMEMBERS</span></div><i>✦</i></div></div>
      <div className="codex-stats" aria-label="Library contents"><span><strong>{CODEX_CLASS_COUNT}</strong> original classes</span><span><strong>{CODEX_SPELL_COUNT}</strong> spell guides</span><span><strong>{entries.length}</strong> topics to explore</span><span className="codex-edition">MORDOR 3.00 · FIELD EDITION</span></div>
      <section className="codex-search-panel" aria-label="Search the codex"><label className="codex-search"><Search size={18}/><input ref={search} aria-label="Search codex topics" placeholder="Search a class, spell, or command…" value={query} maxLength={300} onChange={event => setQuery(event.target.value)}/>{query && <button aria-label="Clear search" onClick={() => { setQuery(''); search.current?.focus(); }}><X size={16}/></button>}</label><div className="codex-filters" role="group" aria-label="Topic categories">{CODEX_CATEGORIES.map(name => { const Icon = icons[name]; return <button key={name} aria-pressed={name === category} onClick={() => filter(name)}><Icon size={13}/>{name}</button>; })}</div></section>
      {category === 'Chronicles' && <div className="codex-kit-notice" role="note"><strong>Server kit required</strong><span>Chronicles are Hollowdeep extensions. Install the kit on your game host to use these commands.</span><a href="/workshop">Get the server kit<ArrowRight size={13}/></a></div>}
      <div className="codex-library">
        <aside className="codex-index" aria-label="Topics"><div className="codex-index-heading"><span>{category === 'All' ? 'THE LIBRARY' : category.toUpperCase()}</span><span role="status">{results.length} topics</span></div><div className="codex-topic-list">{results.map(entry => { const Icon = icons[entry.category]; return <button key={entry.id} aria-current={selected?.id === entry.id ? 'true' : undefined} onClick={() => choose(entry)}><span className="codex-topic-icon"><Icon size={16}/></span><span><strong>{entry.title}</strong><small>{entry.category} · {entry.subtitle}</small>{entry.extension && <small className="codex-kit-label">Server kit required</small>}</span><ChevronRight size={13}/></button>; })}</div>{!results.length && <div className="codex-empty-index"><Search size={22}/><p>No topics found.</p><button onClick={() => { setQuery(''); filter('All'); }}>Clear filters</button></div>}</aside>
        <article ref={article} className="codex-article" tabIndex={-1} aria-label={selected ? `${selected.title} guide` : 'Topic guide'}>
          {selected ? <><div className="codex-article-top"><span><SelectedIcon size={15}/>{selected.category}</span><span>{selected.extension ? 'HOLLOWDEEP EXTENSION' : 'ORIGINAL ENGINE'}</span></div><h2>{selected.title}</h2><p className="codex-subtitle">{selected.subtitle}</p><div className="codex-tags">{selected.tags.map(tag => <span key={tag}>{tag}</span>)}</div><div className="codex-article-rule"><span>✦</span></div><div className="codex-prose">{selected.extension && <div className="codex-extension-note"><strong>Server kit required</strong><p>These additions run after the Hollowdeep server kit is installed on a connected game host. They are separate from stock Mordor 3.00.</p><a href="/workshop">Open server workshop<ArrowRight size={12}/></a></div>}{selected.paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}</div>{selected.id === 'extension-hquest' && <div className="codex-quest-table"><table><caption>Chronicle goals and rewards</caption><thead><tr><th>Chronicle ID</th><th>Places</th><th>Level</th><th>Badge</th></tr></thead><tbody>{CHRONICLE_QUESTS.map(quest => <tr key={quest.id}><th scope="row"><code>{quest.id}</code><small>{quest.title}</small></th><td>{quest.rooms}</td><td>{quest.level}</td><td>{quest.badge}</td></tr>)}</tbody></table></div>}<section className="codex-command-box" aria-label="Command syntax"><span>{selected.category === 'Classes' ? 'CHECK YOUR CHARACTER' : 'AT YOUR COMMAND'}</span><code>{selected.syntax}</code><div><a href={commandHref(selected.command)}>Prepare in terminal<ArrowRight size={14}/></a><button onClick={() => void copy(selected.command)}>{copied === selected.command ? <Check size={14}/> : <Copy size={14}/>}Copy</button></div><p>The command is added to your input for review. You choose when to send it.</p></section>{selected.relatedCommands.length > 0 && <div className="codex-related"><h3>{selected.category === 'Classes' ? 'Explore this calling' : 'Useful companions'}</h3><div>{selected.relatedCommands.map(command => <a key={command} href={commandHref(command)}><code>{command.trim()}{command.endsWith(' ') ? ' …' : ''}</code><ArrowRight size={12}/></a>)}</div></div>}<p className="codex-copy-notice" role="status">{notice}</p><details className="codex-source"><summary>About this guide</summary><p>{selected.extension ? 'Written for the separately installed Hollowdeep additions, based on ' : 'Written for the original Mordor 3.00 rules, based on '}<code>{selected.source}</code>. The running server’s help and your character’s abilities determine what is available. Some actions require a class, level, learned spell, target, or location.</p></details></> : <div className="codex-article-empty"><BookOpen size={43} strokeWidth={1}/><h2>A page yet to be found.</h2><p>Try a shorter search or another category.</p><button onClick={() => { setQuery(''); filter('All'); }}>Browse all topics<ArrowRight size={14}/></button></div>}
        </article>
      </div>
      <section className="codex-builder-note"><div><Code2Mark/><span><strong>A world worth making your own.</strong><p>Open the server workshop to edit command source and export your changes.</p></span></div><a href="/workshop">Shape the realm<ArrowRight size={15}/></a></section>
      <footer className="codex-footer"><span>Original Mordor 3.00 by Brett J. Vickers and Brooke Paul.</span><span>Library guidance · no live character data</span></footer>
    </main>
  </div>;
}

function Code2Mark() { return <span className="codex-builder-mark" aria-hidden="true">{'{ }'}</span>; }
