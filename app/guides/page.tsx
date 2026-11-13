import { ArrowLeft, ArrowRight, BookOpen, Code2, Flame, Shield, Sword, Users } from 'lucide-react';
import './guides.css';

const repo = 'https://github.com/soulkeeper420420/HollowDeep-MUD';
const guides = [
  { title: 'Your first adventure', file: 'PLAYER_GUIDE.md', icon: Sword, text: 'Connect from your phone, choose a class, train, and work through the Chronicles.' },
  { title: 'Care for the realm', file: 'STAFF_GUIDE.md', icon: Shield, text: 'Assign owners, admins, and moderators. Learn the limits of each role and review staff actions.' },
  { title: 'Build and run the server', file: 'SERVER_GUIDE.md', icon: Code2, text: 'Edit the original C engine, test changes, preserve characters, and set up the browser bridge.' },
  { title: 'The Atlas comparison', file: 'ATLAS_COMPARISON.md', icon: Users, text: 'See how Hollowdeep compares with The Secret of Atlas, and which features remain on the roadmap.' },
];
const commands = [
  ['look', 'Read the room and its exits.'], ['score', 'Check your original character statistics.'],
  ['hprofile status', 'A compact view of health, magic, experience, gold, and Chronicle progress.'],
  ['hclass progress', 'See your next training requirements.'], ['hquest next', 'Find the next step in your Chronicles.'],
  ['hstance guarded', 'Trade physical accuracy for defense.'], ['hcommands mobile', 'Short commands for a small screen.'],
  ['hstaff whoami', 'Check your game staff role.'],
];

export default function Guides() {
  return <div className="guides-shell">
    <header className="guides-header"><a className="brand" href="/"><div className="brand-mark"><Flame size={26} strokeWidth={1.25}/></div><div>HOLLOWDEEP<small>THE FIELD GUIDES</small></div></a><a href="/"><ArrowLeft size={16}/>Return to the dungeon</a></header>
    <main className="guides-main">
      <div className="guides-intro"><span>KNOW THE REALM. MAKE IT YOUR OWN.</span><h1>A companion for<br/>every calling.</h1><p>From your first room to your next server update: practical help for adventurers, staff, and builders.</p></div>
      <section className="guides-connect" aria-label="Connection details"><div><span>DIRECT MUD CONNECTION</span><strong>172.233.176.81 <i>:</i> 4040</strong><p>Choose Telnet in your mobile MUD app, Mudlet, or MUSHclient. Log in with your Mordor character.</p></div><a href="/">Open browser client<ArrowRight size={16}/></a></section>
      <p className="guides-release"><BookOpen size={17}/><span>The new stance, staff, and expanded progression commands require the native update on the game host. Browser play also requires the bridge setup. Publishing this guide alone does not install either update.</span></p>
      <div className="guides-grid">{guides.map(({ title, file, icon: Icon, text }, index) => <a className="guides-card" key={file} href={`${repo}/blob/main/docs/${file}`}><div><Icon size={24} strokeWidth={1.3}/><span>0{index + 1}</span></div><h2>{title}</h2><p>{text}</p><strong>Read the guide<ArrowRight size={15}/></strong></a>)}</div>
      <section className="guides-staff"><Code2 size={27}/><div><h2>Move a World Builder draft</h2><p>In the private World Builder, name the draft and choose <strong>Export draft JSON</strong>. In the other browser, choose <strong>Import draft JSON</strong>. The builder validates the area before opening it. Choose <strong>Save Draft</strong> to keep it in that browser.</p><p>Use <strong>Validate &amp; Export ZIP</strong> when you need the native room files for isolated gameplay testing.</p></div></section>
      <section className="guides-commands"><div><span>WORDS THAT OPEN DOORS</span><h2>Keep these close.</h2><p>Select a command to prepare it in the terminal. Review it before sending.</p><a href="/codex">Explore the full codex<ArrowRight size={15}/></a></div><dl>{commands.map(([command, text]) => <div key={command}><dt><a href={`/?command=${encodeURIComponent(command)}`}><code>{command}</code></a></dt><dd>{text}</dd></div>)}</dl></section>
      <section className="guides-staff"><Shield size={27}/><div><h2>Appoint your keepers.</h2><p>After installing the native update, sign in as Realmkeeper and run <code>hstaff whoami</code>. An owner can assign a saved character with <code>hstaff grant Aria admin</code> or <code>hstaff grant Rowan mod</code>. Replace the example names with real characters.</p><p>These roles control the new staff tools. Original Mordor DM powers, website access, and Linux access remain separate.</p></div></section>
      <footer><span>Original Mordor 3.00 by Brett J. Vickers and Brooke Paul.</span><a href={repo}>Source &amp; update history<ArrowRight size={13}/></a></footer>
    </main>
  </div>;
}
