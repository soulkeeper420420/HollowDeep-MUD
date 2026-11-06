'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, BookOpen, Check, Code2, Download, FileCode2, FilePlus2, Flame, FolderOpen, Pencil, RotateCcw, Save, Search, Trash2, Upload, X } from 'lucide-react';
import { WORKBENCH_KEY, MAX_FILE_BYTES, MAX_PROJECT_FILE_BYTES, addFile, changedFiles, createPatch, deleteFile, importTextFiles, parseProject, renameFile, serializeProject, starterProject, updateFile } from '../../lib/workbench.mjs';
import './workshop.css';

type ProjectFile = { path: string; content: string | null; baseContent: string | null };
type Project = { format: string; version: number; name: string; files: ProjectFile[] };
type Pending = { label: string; project: Project } | null;
const fingerprint = (project: Project) => JSON.stringify(project);
function download(text: string, filename: string, type = 'text/plain;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const link = document.createElement('a'); link.href = url; link.download = filename;
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function ServerWorkshop() {
  const [project, setProject] = useState<Project>(() => starterProject());
  const [saved, setSaved] = useState('');
  const [selected, setSelected] = useState('WORKSHOP.md');
  const [ready, setReady] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [filePath, setFilePath] = useState('');
  const [renaming, setRenaming] = useState(false);
  const [undo, setUndo] = useState<Project | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [loadingKit, setLoadingKit] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [findText, setFindText] = useState('');
  const [findMessage, setFindMessage] = useState('');
  const latestProject = useRef(project);
  latestProject.current = project;
  const editor = useRef<HTMLTextAreaElement>(null);
  const importer = useRef<HTMLInputElement>(null);
  const current = project.files.find(file => file.path === selected && file.content !== null);
  const activeFiles = project.files.filter(file => file.content !== null);
  const changes = changedFiles(project);
  const dirty = ready && fingerprint(project) !== saved;
  const lineCount = (current?.content ?? '').split('\n').length;

  useEffect(() => {
    let initial: Project = starterProject();
    try {
      const raw = localStorage.getItem(WORKBENCH_KEY);
      if (raw) { initial = parseProject(raw); setMessage('Saved workshop restored from this browser.'); }
    } catch (err) { setError(`Your saved draft could not be restored. ${err instanceof Error ? err.message : 'Browser storage is unavailable.'}`); }
    setProject(initial); setSaved(fingerprint(initial));
    setSelected(initial.files.find(file => file.content !== null)?.path ?? ''); setReady(true);
  }, []);
  useEffect(() => {
    if (!dirty) return;
    const beforeLeave = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', beforeLeave);
    return () => window.removeEventListener('beforeunload', beforeLeave);
  }, [dirty]);
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') { event.preventDefault(); saveDraft(); }
    };
    document.addEventListener('keydown', key); return () => document.removeEventListener('keydown', key);
  }, [project, ready]);
  function saveDraft() {
    if (!ready) return;
    try { localStorage.setItem(WORKBENCH_KEY, serializeProject(project)); setSaved(fingerprint(project)); setError(''); setMessage('Draft saved in this browser.'); }
    catch { setError('Browser storage is unavailable or full. Download your project to keep these changes.'); }
  }
  function apply(next: Project, notice: string, nextSelected = selected) {
    setProject(next); setSelected(nextSelected); setError(''); setMessage(notice);
  }
  function replace(next: Project, notice: string) {
    setUndo(project); apply(next, notice, next.files.find(file => file.content !== null)?.path ?? ''); setPending(null);
  }
  function requestReplace(next: Project, label: string) { setPending({ project: next, label }); setError(''); }
  function createOrRename(event: React.FormEvent) {
    event.preventDefault();
    try {
      const path = filePath.trim();
      const next = renaming ? renameFile(project, selected, path) : addFile(project, path);
      setUndo(project); apply(next, renaming ? 'File renamed. The exported patch includes the new path.' : 'File created.', path);
      setFilePath(''); setRenaming(false);
    } catch (err) { setError(err instanceof Error ? err.message : 'The file could not be changed.'); }
  }
  function removeCurrent() {
    if (!current) return;
    const next: Project = deleteFile(project, current.path); setUndo(project);
    apply(next, 'File removed from this draft. Undo is available.', next.files.find(file => file.content !== null)?.path ?? '');
  }
  async function importFiles(files: FileList | null) {
    if (!files?.length) return;
    try {
      const chosen = Array.from(files);
      if (chosen.length === 1 && chosen[0].name.endsWith('.json')) {
        if (chosen[0].size > MAX_PROJECT_FILE_BYTES) throw new Error('The project import is too large.');
        const raw = await chosen[0].text();
        let candidate;
        try { candidate = JSON.parse(raw); } catch { /* Plain JSON files can still be edited. */ }
        if (candidate?.format === 'hollowdeep-workshop') { requestReplace(parseProject(raw), 'Import project'); return; }
      }
      if (chosen.some(file => file.size > MAX_FILE_BYTES)) throw new Error('Each imported source file must be smaller than 384 KB.');
      const entries = await Promise.all(chosen.map(async file => ({ path: file.webkitRelativePath || file.name, content: await file.text() })));
      const before = latestProject.current;
      const next = importTextFiles(before, entries); setUndo(before);
      apply(next, `${entries.length} source file${entries.length === 1 ? '' : 's'} imported. Their current contents are the patch baseline.`, entries[0].path);
    } catch (err) { setError(err instanceof Error ? err.message : 'The import could not be read.'); }
    finally { if (importer.current) importer.current.value = ''; }
  }
  async function loadKit() {
    setLoadingKit(true); setError('');
    try {
      const response = await fetch('/workshop-files/index.json', { cache: 'no-store' });
      if (!response.ok) throw new Error('The server kit is not available. You can still import source files.');
      const raw = await response.text();
      requestReplace(parseProject(raw), 'Load server kit');
    } catch (err) { setError(err instanceof Error ? err.message : 'The server kit could not be loaded.'); }
    finally { setLoadingKit(false); }
  }
  function exportProject() {
    try { download(serializeProject(project), 'hollowdeep-workshop.json', 'application/json'); setMessage('Project download prepared. It includes original copies for patch export.'); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'The project could not be exported.'); }
  }
  function exportPatch() {
    try { const patch = createPatch(project); if (!patch) return; download(patch, 'hollowdeep-server.patch', 'text/x-diff'); setMessage('Patch prepared. Apply it to the matching source checkout, then build and test.'); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'The patch could not be exported.'); }
  }
  function findNext() {
    if (!current || !findText || !editor.current) return;
    const text = current.content ?? ''; const from = editor.current.selectionEnd;
    let index = text.toLocaleLowerCase().indexOf(findText.toLocaleLowerCase(), from);
    if (index < 0) index = text.toLocaleLowerCase().indexOf(findText.toLocaleLowerCase());
    if (index < 0) { setFindMessage('No matches in this file.'); return; }
    editor.current.focus(); editor.current.setSelectionRange(index, index + findText.length);
    const row = text.slice(0, index).split('\n').length;
    editor.current.scrollTop = Math.max(0, (row - 3) * 22); setFindMessage(`Match on line ${row}.`);
  }
  function editText(value: string) {
    if (!current) return;
    try { setProject(updateFile(project, current.path, value)); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'The file could not be edited.'); }
  }

  return <div className="workshop-shell">
    <header className="workshop-header"><a className="brand" href="/"><div className="brand-mark"><Flame size={26} strokeWidth={1.25}/></div><div>HOLLOWDEEP<small>SERVER WORKSHOP</small></div></a><a className="workshop-back" href="/"><ArrowLeft size={15}/>Back to the dungeon</a></header>
    <main className="workshop-main">
      <div className="workshop-heading"><div><span className="workshop-eyebrow">BUILD YOUR REALM</span><h1>Shape the next chapter.</h1><p>Edit server source, keep a draft, and take your changes back to the original Mordor engine.</p></div><button className="workshop-guide-toggle" onClick={() => setShowGuide(value => !value)} aria-expanded={showGuide}><BookOpen size={17}/>{showGuide ? 'Close guide' : 'Development guide'}</button></div>
      <div className="workshop-local-note"><Code2 size={17}/><span><strong>Your coding workspace.</strong> Files stay in this browser until you download them. Saving here does not update the live game.</span></div>
      <p className="workshop-local-note"><a href="/guides">Player &amp; staff guides</a> · <a href="https://github.com/soulkeeper420420/HollowDeep-MUD">Source on GitHub</a></p><div className="workshop-kit-banner"><div><strong>Take the server with you.</strong><p>Original Mordor source, editable C extensions, build tools, and the browser bridge. Requires Linux with a 32-bit GCC toolchain.</p></div><a href="/workshop-files/hollowdeep-server-kit.tar.gz" download><Download size={16}/>Download server kit</a></div>
      {showGuide && <section className="workshop-guide" aria-label="Server development guide"><div><span>01</span><h2>Start with the source</h2><p>Load the server kit for editable Hollowdeep command files and build instructions. Import other text files to work on your own code. Imported files become the original version used for patches.</p></div><div><span>02</span><h2>Edit and keep a copy</h2><p>Save drafts on this device with <kbd>Ctrl / ⌘ S</kbd>. Download the project to transfer it to another browser. Export a patch when you are ready to move code into your server checkout.</p></div><div><span>03</span><h2>Build, test, then update</h2><p>Use the server kit’s README to apply your patch, compile Mordor, and test on a development port. Back up the game’s player files before replacing a running server.</p></div></section>}
      <div className="workshop-actions"><div className="workshop-status"><span className={dirty ? 'unsaved' : ''}/>{!ready ? 'Loading draft…' : dirty ? 'Unsaved changes' : 'Draft up to date'}<small>{changes.length} changed file{changes.length === 1 ? '' : 's'}</small></div><button disabled={!ready} onClick={saveDraft} className="workshop-primary"><Save size={14}/>Save draft</button><button disabled={!ready} onClick={exportProject}><Download size={14}/>Download project</button><button disabled={!ready || !changes.length} onClick={exportPatch}><FileCode2 size={14}/>Export patch</button></div>
      {pending && <div className="workshop-confirm" role="alert"><div><strong>{pending.label}?</strong><p>This replaces the open workspace. Download your current project first if you want a separate copy.</p></div><button onClick={() => replace(pending.project, `${pending.label} complete. Save your draft to keep it in this browser.`)}>{pending.label}<ArrowRight size={14}/></button><button onClick={() => setPending(null)}>Cancel</button></div>}
      {(message || error || undo) && <div className={'workshop-feedback' + (error ? ' has-error' : '')}><p role={error ? 'alert' : 'status'}>{error || message}</p>{undo && <button onClick={() => { const previous = undo; setUndo(null); apply(previous, 'Previous workspace restored.', previous.files.find(file => file.content !== null)?.path ?? ''); }}><RotateCcw size={13}/>Undo last file action</button>}</div>}
      <div className="workshop-workspace">
        <aside className="workshop-files" aria-label="Project files"><div className="workshop-file-heading"><FolderOpen size={16}/><strong>Project files</strong><span>{activeFiles.length}</span></div><div className="workshop-source-buttons"><button disabled={!ready || loadingKit} onClick={loadKit}><Code2 size={13}/>{loadingKit ? 'Loading…' : 'Load server kit'}</button><button disabled={!ready} onClick={() => importer.current?.click()}><Upload size={13}/>Import files</button><input ref={importer} type="file" multiple accept=".c,.h,.md,.json,.sh,.txt,.patch,.cfg,.ini,.conf,.py,.js,.mjs,.ts,.tsx,.css,.html,.lua,.mk" hidden onChange={event => void importFiles(event.target.files)}/></div><nav className="workshop-file-list" aria-label="Choose source file">{activeFiles.map(file => <button key={file.path} onClick={() => { setSelected(file.path); setRenaming(false); setFilePath(''); setFindMessage(''); }} aria-current={selected === file.path ? 'true' : undefined}><FileCode2 size={14}/><span>{file.path}</span>{file.content !== file.baseContent && <i aria-label="Changed"/>}</button>)}{!activeFiles.length && <p className="workshop-empty-files">Create a file or load the server kit to begin.</p>}</nav><form className="workshop-new-file" onSubmit={createOrRename}><label htmlFor="workshop-path">{renaming ? 'Rename selected file' : 'New file path'}</label><div><input id="workshop-path" value={filePath} onChange={event => setFilePath(event.target.value)} maxLength={160} placeholder="src/my_command.c" autoCapitalize="none" autoCorrect="off"/><button disabled={!ready || !filePath.trim()} title={renaming ? 'Rename file' : 'Create file'} aria-label={renaming ? 'Rename file' : 'Create file'}>{renaming ? <Check size={16}/> : <FilePlus2 size={16}/>}</button></div>{renaming && <button type="button" className="workshop-cancel-rename" onClick={() => { setRenaming(false); setFilePath(''); }}><X size={12}/>Cancel rename</button>}</form><div className="workshop-file-footer">C · headers · text · JSON<br/>80 files · 384 KB per file<br/>4 MB including originals</div></aside>
        <section className="workshop-editor" aria-label="Source editor"><div className="workshop-editor-heading"><div><Code2 size={15}/><strong>{current?.path ?? 'No file selected'}</strong></div><div className="workshop-editor-controls"><button disabled={!current} title="Download selected file" aria-label="Download selected file" onClick={() => current && download(current.content ?? '', current.path.split('/').at(-1) ?? 'source.txt')}><Download size={15}/></button><button disabled={!current} title="Rename selected file" aria-label="Rename selected file" onClick={() => { setRenaming(true); setFilePath(current?.path ?? ''); }}><Pencil size={15}/></button><button disabled={!current} title="Delete selected file" aria-label="Delete selected file" onClick={removeCurrent}><Trash2 size={15}/></button></div></div><form className="workshop-find" onSubmit={event => { event.preventDefault(); findNext(); }}><Search size={13}/><input aria-label="Find in current file" value={findText} onChange={event => { setFindText(event.target.value); setFindMessage(''); }} placeholder="Find in file…"/><button disabled={!current || !findText}>Find next</button><span role="status">{findMessage}</span></form>{current ? <textarea ref={editor} className="workshop-code" aria-label={`Source code for ${current.path}`} value={current.content ?? ''} onChange={event => editText(event.target.value)} spellCheck={false} autoCapitalize="none" autoCorrect="off" wrap="off" onKeyDown={event => { if (event.key === 'Tab' && !event.shiftKey) { event.preventDefault(); const start = event.currentTarget.selectionStart, end = event.currentTarget.selectionEnd; const text = current.content ?? ''; editText(text.slice(0, start) + '  ' + text.slice(end)); requestAnimationFrame(() => editor.current?.setSelectionRange(start + 2, start + 2)); } }}/>: <div className="workshop-editor-empty"><FileCode2 size={36}/><h2>A new idea starts here.</h2><p>Create a file, import source, or load the server kit.</p></div>}<div className="workshop-editor-footer"><span>{current ? `${lineCount.toLocaleString()} lines · ${new TextEncoder().encode(current.content ?? '').length.toLocaleString()} bytes` : 'Text files only'}</span><span>UTF-8 · Tab indents · Shift+Tab leaves editor</span></div></section>
      </div>
      <footer className="workshop-footer"><p>Original Mordor 3.00 remains the game server. This workshop prepares files and patches; builds and server updates happen on your development machine or host.</p><button onClick={() => requestReplace(starterProject(), 'Reset workshop')}>Reset to starter guide<RotateCcw size={12}/></button></footer>
    </main>
  </div>;
}
