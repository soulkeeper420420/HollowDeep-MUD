'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowRight, BookOpen, Check, Copy, Download, Plus, Search, Star, Trash2, MessageCircle, Swords } from 'lucide-react';
import { composeCombat, composeSocial, connectionText, createPreferenceStore, filterCommands, journalText, readFavorites, readJournal } from '../../lib/client-utils.mjs';
import './ClientTools.css';

type Note = { id: string; text: string; createdAt: string };
const CATEGORIES = ['All', 'Favorites', 'Navigation', 'Information', 'Social', 'Combat', 'Items', 'Progression', 'Chronicles'];
const favoriteStore = createPreferenceStore('hollowdeep-favorites');
const journalStore = createPreferenceStore('hollowdeep-journal');
function browserStorage() { try { return window.localStorage; } catch { return undefined; } }

function downloadText(text: string, filename: string) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
  const link = document.createElement('a'); link.href = url; link.download = filename;
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function CommandPalette({ onSelect }: { onSelect: (command: string) => void }) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('All');
  const [favorites, setFavorites] = useState<string[]>([]);
  const [notice, setNotice] = useState('');
  useEffect(() => {
    const storage = browserStorage();
    setFavorites(favoriteStore.read(storage, readFavorites));
    if (!storage) setNotice('Favorites will last for this visit; browser storage is unavailable.');
  }, []);
  function toggleFavorite(id: string) {
    const next = favorites.includes(id) ? favorites.filter(item => item !== id) : [...favorites, id];
    setFavorites(next);
    if (!favoriteStore.write(browserStorage(), next)) setNotice('Favorites will last for this visit; browser storage is unavailable.');
  }
  const commands = filterCommands(query, category, favorites);
  return <div className="client-tools command-palette">
    <p>Find a command, then add it to your command line. Review it before pressing Enter.</p>
    <label className="command-search"><Search size={16}/><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search commands, actions, or descriptions…" aria-label="Search commands" autoComplete="off"/></label>
    <div className="command-categories" role="group" aria-label="Command categories">{CATEGORIES.map(name => <button key={name} aria-pressed={category === name} onClick={() => setCategory(name)}>{name === 'Favorites' && <Star size={11}/>} {name}</button>)}</div>
    {category === 'Social' && <SocialComposer onSelect={onSelect}/>}
    {category === 'Combat' && <CombatComposer onSelect={onSelect}/>}
    <div className="command-results" aria-live="polite">{commands.length} command{commands.length === 1 ? '' : 's'}</div>
    <div className="command-list">{commands.map(command => <div className="command-item" key={command.id}>
      <button className="command-pick" onClick={() => onSelect(command.command)} aria-label={`Add ${command.label.toLowerCase()} to command line`}><div><code>{command.command.trim()}{command.template && <span> …</span>}</code><span className="command-category-label">{command.category}</span></div><strong>{command.label}</strong><p>{command.description}</p><span className="command-fill">{command.caution ? 'Review before sending' : 'Add to command line'}<ArrowRight size={12}/></span></button>
      <button className={'favorite-command ' + (favorites.includes(command.id) ? 'is-favorite' : '')} onClick={() => toggleFavorite(command.id)} aria-label={`${favorites.includes(command.id) ? 'Unfavorite' : 'Favorite'} ${command.label.toLowerCase()}`} aria-pressed={favorites.includes(command.id)}><Star size={15} fill={favorites.includes(command.id) ? 'currentColor' : 'none'}/></button>
    </div>)}</div>
    {!commands.length && <div className="tools-empty"><Search size={22}/><h3>{category === 'Favorites' && !query ? 'Your favorite commands go here.' : 'No commands found.'}</h3><p>{category === 'Favorites' && !query ? 'Use the star beside a command to keep it close at hand.' : 'Try another word or choose a different category.'}</p></div>}
    {notice && <p className="tools-notice" role="status">{notice}</p>}
    <p className="tools-fine-print">These shortcuts send commands to Mordor. Use <code>help</code> in the game for its full rules and command syntax.</p>
  </div>;
}

export function AdventureJournal() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [draft, setDraft] = useState('');
  const [message, setMessage] = useState('');
  const [loaded, setLoaded] = useState(false);
  const [removed, setRemoved] = useState<{ note: Note; index: number } | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    const storage = browserStorage();
    setNotes(journalStore.read(storage, readJournal));
    if (!storage) setMessage('Browser storage is unavailable. Export your notes before leaving.');
    setLoaded(true);
  }, []);
  function persist(next: Note[], success: string) {
    setNotes(next);
    setMessage(journalStore.write(browserStorage(), next) ? success : 'Your notes are in this tab only. Export them before leaving.');
  }
  function addNote(event: React.FormEvent) {
    event.preventDefault();
    if (!draft.trim() || notes.length >= 100) return;
    const note = { id: crypto.randomUUID(), text: draft.trim(), createdAt: new Date().toISOString() };
    persist([note, ...notes], 'Note saved in this browser.'); setDraft(''); setRemoved(null); inputRef.current?.focus();
  }
  function removeNote(note: Note, index: number) {
    setRemoved({ note, index }); persist(notes.filter(item => item.id !== note.id), 'Note removed. You can undo this below.');
  }
  function undoRemove() {
    if (!removed || notes.length >= 100) return;
    const next = [...notes]; next.splice(Math.min(removed.index, next.length), 0, removed.note);
    persist(next, 'Note restored.'); setRemoved(null);
  }
  return <div className="client-tools adventure-journal">
    <p>Keep room clues, plans, and stories from your travels. This journal belongs to this browser; it does not change your character.</p>
    <form onSubmit={addNote}><label htmlFor="adventure-note">A note for the road</label><textarea id="adventure-note" ref={inputRef} value={draft} onChange={event => setDraft(event.target.value)} maxLength={4000} rows={4} placeholder="A path to remember. A promise to keep…"/><div className="journal-form-footer"><span>{draft.length.toLocaleString()} / 4,000</span><button type="submit" disabled={!loaded || !draft.trim() || notes.length >= 100}><Plus size={14}/>Save note</button></div></form>
    <div className="journal-toolbar"><span>{notes.length} / 100 notes</span><button disabled={!notes.length} onClick={() => { try { downloadText(journalText(notes), 'hollowdeep-journal.txt'); setMessage('Journal export prepared.'); } catch { setMessage('The download could not start. Your notes are still shown below.'); } }}><Download size={14}/>Export journal</button></div>
    {notes.length >= 100 && <p className="tools-notice">Your journal is full. Export it, then remove an old note to make room.</p>}
    <div className="journal-feedback" aria-live="polite"><span>{message}</span>{removed && <button onClick={undoRemove}>Undo removal</button>}</div>
    <div className="journal-notes">{notes.map((note, index) => <article className="journal-note" key={note.id}><div><time dateTime={note.createdAt}>{new Date(note.createdAt).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}</time><button onClick={() => removeNote(note, index)} aria-label={`Remove note from ${new Date(note.createdAt).toLocaleString()}`}><Trash2 size={14}/></button></div><p>{note.text}</p></article>)}</div>
    {loaded && !notes.length && <div className="tools-empty"><BookOpen size={25}/><h3>The first page is yours.</h3><p>Add a note above to begin your journal.</p></div>}
    <p className="tools-fine-print">Notes are stored on this device, not shared with other players. Export a copy to keep them when switching browsers.</p>
  </div>;
}

export function NativeConnectionTools({ host, port }: { host: string; port: number }) {
  const [notice, setNotice] = useState('');
  let text: string;
  try { text = connectionText(host, port); }
  catch { return <p className="tools-notice">The public MUD connection details are not configured correctly.</p>; }
  return <div className="client-tools native-connection-tools"><dl className="native-details"><div><dt>Server hostname</dt><dd><code>{host}</code></dd></div><div><dt>Port</dt><dd><code>{port}</code></dd></div><div><dt>Protocol</dt><dd>Telnet · ANSI</dd></div></dl><div className="connection-actions"><button onClick={async () => { try { await navigator.clipboard.writeText(`${host}:${port}`); setNotice('Server address copied.'); } catch { setNotice('Clipboard unavailable. Use the hostname and port shown above.'); } }}>{notice === 'Server address copied.' ? <Check size={14}/> : <Copy size={14}/>}Copy address</button><button onClick={() => { try { downloadText(text, 'hollowdeep-mud-connection.txt'); setNotice('Connection instructions prepared for download.'); } catch { setNotice('The download could not start. Use the hostname and port shown above.'); } }}><Download size={14}/>Download instructions</button></div><p role="status" className="tools-fine-print">{notice}</p></div>;
}

export function SocialComposer({ onSelect }: { onSelect: (command: string) => void }) {
  const [channel, setChannel] = useState('say');
  const [target, setTarget] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const result = composeSocial(channel, target, message);
  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!result.ok || !('command' in result)) { setError('error' in result && result.error ? result.error : 'Complete the message first.'); return; }
    onSelect(result.command);
  }
  return <form className="action-composer" onSubmit={submit}><div className="composer-title"><MessageCircle size={15}/><h3>Start a conversation</h3></div><label>Where to speak<select value={channel} onChange={event => { setChannel(event.target.value); setError(''); }}><option value="say">To the room</option><option value="tell">To an adventurer</option><option value="gtalk">To your group</option><option value="emote">Roleplay an action</option></select></label>{channel === 'tell' && <label>Character name<input value={target} maxLength={30} autoCapitalize="none" autoComplete="off" onChange={event => { setTarget(event.target.value); setError(''); }} placeholder="A fellow adventurer’s name"/></label>}<label>Message<input value={message} maxLength={256} onChange={event => { setMessage(event.target.value); setError(''); }} placeholder={channel === 'emote' ? 'raises a lantern and studies the doorway.' : channel === 'gtalk' ? 'Stay together. Which passage shall we take?' : 'Hail, traveler. Shall we explore together?'}/></label>{result.ok && 'command' in result && <div className="command-preview"><span>Command preview</span><code>{result.command}</code></div>}{error && <p className="tools-notice" role="alert">{error}</p>}<div className="composer-footer"><span>Added to your command line for review.</span><button type="submit">Prepare message<ArrowRight size={13}/></button></div></form>;
}

export function CombatComposer({ onSelect }: { onSelect: (command: string) => void }) {
  const [action, setAction] = useState('kill');
  const [target, setTarget] = useState('');
  const [error, setError] = useState('');
  const result = composeCombat(action, target);
  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!result.ok || !('command' in result)) { setError('error' in result && result.error ? result.error : 'Complete the action first.'); return; }
    onSelect(result.command);
  }
  return <form className="action-composer" onSubmit={submit}><div className="composer-title"><Swords size={15}/><h3>Plan your next move</h3></div><label>Action<select value={action} onChange={event => { setAction(event.target.value); setTarget(''); setError(''); }}><option value="kill">Attack a creature</option><option value="cast">Cast a spell</option></select></label><label>{action === 'kill' ? 'Creature name' : 'Spell and target'}<input value={target} maxLength={251} onChange={event => { setTarget(event.target.value); setError(''); }} placeholder={action === 'kill' ? 'Use the name shown by the game' : 'Use Mordor’s spell syntax from help'}/></label>{result.ok && 'command' in result && <div className="command-preview"><span>Command preview</span><code>{result.command}</code></div>}{error && <p className="tools-notice" role="alert">{error}</p>}<div className="composer-footer"><span>Review the target before pressing Enter.</span><button type="submit">Prepare action<ArrowRight size={13}/></button></div><p className="tools-fine-print">This prepares a command; it does not attack automatically. Your character’s class, learned spells, and progression are managed by Mordor.</p></form>;
}
