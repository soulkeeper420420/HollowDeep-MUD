'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Check, ChevronLeft, ChevronRight, Download, Edit3, Plus, Save, Target, Trash2, Upload, WandSparkles, X } from 'lucide-react';
import { emptyProfile, expandTemplate, exportProfile, getWorkshopProfile, LIMITS, parseProfile, saveWorkshopProfile, starterProfile, validateProfile } from '../../lib/command-workshop.mjs';
import './CommandWorkshop.css';

type Alias = { name: string; template: string };
type Macro = { name: string; steps: string[] };
type Profile = { version: number; target: string; aliases: Alias[]; macros: Macro[] };
let lastMacro = '';
let lastStep = 0;
function storage() { try { return window.localStorage; } catch { return undefined; } }
function download(text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: 'application/json;charset=utf-8' }));
  const link = document.createElement('a'); link.href = url; link.download = 'hollowdeep-command-profile.json';
  document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function CommandWorkshop({ onPrepare, hiddenInput = false }: { onPrepare: (command: string) => void; hiddenInput?: boolean }) {
  const [profile, setProfile] = useState<Profile>(emptyProfile());
  const [loaded, setLoaded] = useState(false);
  const [tab, setTab] = useState<'aliases' | 'macros' | 'profiles'>('aliases');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [target, setTarget] = useState('');
  const [editName, setEditName] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [body, setBody] = useState('');
  const [aliasName, setAliasName] = useState('');
  const [args, setArgs] = useState('');
  const [macroName, setMacroName] = useState(lastMacro);
  const [step, setStep] = useState(lastStep);
  const [imported, setImported] = useState<Profile | null>(null);
  const [removed, setRemoved] = useState<Profile | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const saved = getWorkshopProfile(storage()); setProfile(saved); setTarget(saved.target); setLoaded(true);
    setAliasName(saved.aliases[0]?.name ?? '');
    const macro = saved.macros.find((item: Macro) => item.name === lastMacro) ?? saved.macros[0];
    setMacroName(macro?.name ?? ''); setStep(Math.min(lastStep, Math.max(0, (macro?.steps.length ?? 1) - 1)));
  }, []);
  function persist(next: Profile, message: string) {
    const result = saveWorkshopProfile(next, storage());
    if (!result.ok) { setError(result.error ?? 'Check your profile.'); return false; }
    setProfile(next); setError(''); setNotice(result.persistent ? message : `${message} Kept for this visit only; export a copy before leaving.`);
    return true;
  }
  function resetEditor() { setEditName(null); setName(''); setBody(''); }
  function switchTab(next: typeof tab) { setTab(next); resetEditor(); setError(''); }
  function saveEntry(event: React.FormEvent) {
    event.preventDefault();
    const normalizedName = name.trim();
    let next: Profile;
    if (tab === 'aliases') {
      if (profile.aliases.some(item => item.name === normalizedName && item.name !== editName)) { setError('An alias already uses that name.'); return; }
      const item = { name: normalizedName, template: body };
      next = { ...profile, aliases: editName ? profile.aliases.map(old => old.name === editName ? item : old) : [...profile.aliases, item] };
    } else {
      if (profile.macros.some(item => item.name === normalizedName && item.name !== editName)) { setError('A macro already uses that name.'); return; }
      const item = { name: normalizedName, steps: body.split('\n') };
      next = { ...profile, macros: editName ? profile.macros.map(old => old.name === editName ? item : old) : [...profile.macros, item] };
    }
    const valid = validateProfile(next); if (!valid.ok) { setError(valid.error ?? 'Check your command.'); return; }
    if (persist(next, `${tab === 'aliases' ? 'Alias' : 'Macro'} saved.`)) {
      if (tab === 'aliases') setAliasName(normalizedName);
      else { setMacroName(normalizedName); setStep(0); lastMacro = normalizedName; lastStep = 0; }
      resetEditor(); setRemoved(null);
    }
  }
  function prepare(command: string) {
    if (hiddenInput) { setError('Finish the hidden login or password prompt before preparing game commands.'); return; }
    onPrepare(command);
  }
  function remove(kind: 'aliases' | 'macros', entryName: string) {
    setRemoved(profile);
    persist({ ...profile, [kind]: profile[kind].filter(item => item.name !== entryName) }, 'Removed. Use Undo to restore it.');
    if (editName === entryName) resetEditor();
    if (kind === 'aliases' && aliasName === entryName) setAliasName('');
    if (kind === 'macros' && macroName === entryName) { setMacroName(''); setStep(0); lastMacro = ''; lastStep = 0; }
  }
  async function readImport(file: File | undefined) {
    if (!file) return;
    setImported(null);
    if (file.size > LIMITS.fileBytes) { setError('Choose a JSON profile smaller than 32 KB.'); return; }
    try { const result = parseProfile(await file.text()); if (!result.ok) setError(result.error ?? 'Cannot import this profile.'); else { setImported(result.profile as Profile); setError(''); } }
    catch { setError('The file could not be read.'); }
  }
  const selectedAlias = profile.aliases.find(item => item.name === aliasName);
  const selectedMacro = profile.macros.find(item => item.name === macroName);
  const preview = expandTemplate(tab === 'aliases' ? selectedAlias?.template ?? '' : selectedMacro?.steps[step] ?? '', args, profile.target);
  const list = tab === 'aliases' ? profile.aliases : profile.macros;

  return <div className="command-workshop">
    <p>Make the command line your own. Shortcuts prepare one command for review; you press Enter to send it.</p>
    <form className="workshop-target" onSubmit={event => { event.preventDefault(); persist({ ...profile, target }, 'Target saved.'); }}>
      <label htmlFor="workshop-target"><Target size={15}/>Current target</label>
      <div><input id="workshop-target" value={target} onChange={event => setTarget(event.target.value)} maxLength={60} placeholder="Creature, item, or character name" autoComplete="off"/><button type="submit" disabled={!loaded}><Save size={14}/>Save</button></div>
      <span>Use <code>$target</code> in any shortcut. Saved target: {profile.target || 'none'}.</span>
    </form>
    <div className="workshop-tabs" role="group" aria-label="Command workshop sections">{(['aliases', 'macros', 'profiles'] as const).map(item => <button key={item} aria-pressed={tab === item} onClick={() => switchTab(item)}>{item === 'aliases' ? 'Aliases' : item === 'macros' ? 'Step-by-step macros' : 'Import & export'}</button>)}</div>
    {hiddenInput && <p className="workshop-notice">Command preparation is paused during hidden input. Finish your login prompt first.</p>}
    {error && <p className="workshop-error" role="alert">{error}</p>}
    <div className="workshop-feedback" role="status">{notice}{removed && <button onClick={() => { if (persist(removed, 'Previous profile restored.')) { setTarget(removed.target); setRemoved(null); } }}>Undo</button>}</div>
    {tab !== 'profiles' && <>
      <div className="workshop-saved">
        <div className="workshop-heading"><h3>{tab === 'aliases' ? 'Your aliases' : 'Your macros'}</h3><span>{list.length} / {tab === 'aliases' ? LIMITS.aliases : LIMITS.macros}</span></div>
        {list.length === 0 ? <div className="workshop-empty"><WandSparkles size={21}/><p>{tab === 'aliases' ? 'Give a frequently used command a short name.' : 'Keep a routine in order, one deliberate step at a time.'}</p><button onClick={() => { const starters = starterProfile(); const next = tab === 'aliases' ? { ...profile, aliases: starters.aliases } : { ...profile, macros: starters.macros }; if (persist(next, 'Starter commands added.')) { setAliasName(next.aliases[0]?.name ?? ''); setMacroName(next.macros[0]?.name ?? ''); setStep(0); } }}>Add starter {tab}</button></div> : <ul>{list.map(item => <li key={item.name}><div><strong>{tab === 'aliases' ? '/' : ''}{item.name}</strong><code>{'template' in item ? item.template : `${item.steps.length} steps · ${item.steps[0]}`}</code></div><button aria-label={`Edit ${item.name}`} onClick={() => { setEditName(item.name); setName(item.name); setBody('template' in item ? item.template : item.steps.join('\n')); }}><Edit3 size={14}/></button><button aria-label={`Remove ${item.name}`} onClick={() => remove(tab as 'aliases' | 'macros', item.name)}><Trash2 size={14}/></button></li>)}</ul>}
      </div>
      <form className="workshop-editor" onSubmit={saveEntry}>
        <div className="workshop-heading"><h3>{editName ? 'Edit' : 'Create'} {tab === 'aliases' ? 'alias' : 'macro'}</h3>{editName && <button type="button" onClick={resetEditor}><X size={13}/>Cancel edit</button>}</div>
        <label>Name<input value={name} onChange={event => setName(event.target.value)} maxLength={24} autoComplete="off" autoCapitalize="none" spellCheck={false} placeholder={tab === 'aliases' ? 'strike' : 'check-in'}/></label>
        <label>{tab === 'aliases' ? 'Command template' : 'Commands — one per line'}{tab === 'aliases' ? <input value={body} onChange={event => setBody(event.target.value)} maxLength={256} autoComplete="off" spellCheck={false} placeholder="kill $target"/> : <textarea value={body} onChange={event => setBody(event.target.value)} maxLength={3083} rows={4} spellCheck={false} placeholder={'look\nscore\ninventory'}/>}</label>
        <p className="workshop-help"><code>$1</code> through <code>$9</code> insert words, <code>$*</code> inserts all arguments, <code>$target</code> inserts your saved target, and <code>$$</code> inserts a dollar sign. Arguments are separated by spaces.</p>
        <button className="workshop-primary" type="submit" disabled={!loaded || !name || !body}>{editName ? <Save size={14}/> : <Plus size={14}/>}{editName ? 'Save changes' : `Create ${tab === 'aliases' ? 'alias' : 'macro'}`}</button>
      </form>
      {list.length > 0 && <div className="workshop-runner">
        <h3>{tab === 'aliases' ? 'Prepare an alias' : 'Walk through a macro'}</h3>
        <label>{tab === 'aliases' ? 'Alias' : 'Macro'}<select value={tab === 'aliases' ? aliasName : macroName} onChange={event => { if (tab === 'aliases') setAliasName(event.target.value); else { setMacroName(event.target.value); lastMacro = event.target.value; setStep(0); lastStep = 0; } }}><option value="">Choose a {tab === 'aliases' ? 'shortcut' : 'macro'}</option>{list.map(item => <option key={item.name} value={item.name}>{item.name}</option>)}</select></label>
        <label>Arguments<input value={args} onChange={event => setArgs(event.target.value)} maxLength={256} autoComplete="off" placeholder="Optional words for $1 or $*"/></label>
        {tab === 'macros' && selectedMacro && <div className="workshop-steps"><button aria-label="Previous macro step" disabled={step === 0} onClick={() => { setStep(step - 1); lastStep = step - 1; }}><ChevronLeft size={15}/></button><span>Step {step + 1} of {selectedMacro.steps.length}</span><button aria-label="Next macro step" disabled={step >= selectedMacro.steps.length - 1} onClick={() => { setStep(step + 1); lastStep = step + 1; }}><ChevronRight size={15}/></button></div>}
        <div className="workshop-preview"><span>Command preview</span>{preview.ok && 'command' in preview ? <code>{preview.command}</code> : <p>{(selectedAlias && tab === 'aliases') || (selectedMacro && tab === 'macros') ? preview.error : 'Choose a shortcut to preview it.'}</p>}</div>
        <button className="workshop-primary" disabled={!preview.ok || hiddenInput} onClick={() => { if (preview.ok && 'command' in preview) prepare(preview.command); }}>Prepare {tab === 'aliases' ? 'command' : 'this step'}<ArrowRight size={14}/></button>
        {tab === 'macros' && <p className="workshop-help">Return here and choose the next step after sending your command. Nothing advances or runs automatically.</p>}
      </div>}
    </>}
    {tab === 'profiles' && <div className="workshop-transfer"><h3>Take your shortcuts with you</h3><p>Profiles contain your aliases, macros, and target. Command history, game output, and login replies are never included. Do not put passwords in templates.</p><div className="workshop-transfer-actions"><button disabled={!loaded} onClick={() => { const result = exportProfile(profile); if (result.ok && 'text' in result) { try { download(result.text); setNotice('Profile exported.'); } catch { setError('Your browser could not start the download.'); } } else setError(result.error ?? 'Cannot export this profile.'); }}><Download size={15}/>Export profile</button><button onClick={() => fileRef.current?.click()}><Upload size={15}/>Choose JSON file</button><input ref={fileRef} type="file" accept="application/json,.json" aria-label="Import command profile" onChange={event => { void readImport(event.target.files?.[0]); event.target.value = ''; }} hidden/></div>{imported && <div className="workshop-import"><Check size={17}/><h4>Profile ready to import</h4><p>{imported.aliases.length} aliases · {imported.macros.length} macros · Target: {imported.target || 'none'}</p><p>This replaces your current command profile. Export a copy first if you want to keep it.</p><div><button className="workshop-primary" onClick={() => { setRemoved(profile); if (persist(imported, 'Profile imported.')) { setTarget(imported.target); setAliasName(imported.aliases[0]?.name ?? ''); setMacroName(imported.macros[0]?.name ?? ''); setStep(0); lastMacro = imported.macros[0]?.name ?? ''; lastStep = 0; setImported(null); resetEditor(); } }}>Replace with this profile</button><button onClick={() => setImported(null)}>Cancel</button></div></div>}</div>}
    <p className="workshop-help workshop-local">Saved in this browser. These tools prepare game commands; they do not change server rules or run scripts.</p>
  </div>;
}
