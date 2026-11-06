import { createHash } from 'node:crypto';
import { mkdtemp, readFile, readdir, mkdir, copyFile, writeFile, rm } from 'node:fs/promises';
import { join, relative, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import { serializeProject } from '../lib/workbench.mjs';

const root = process.cwd();
const archive = process.argv[2];
if (!archive) throw new Error('Usage: node scripts/package-server-kit.mjs /path/to/Mordor_3.00.tar.gz');
const sha = createHash('sha256').update(await readFile(archive)).digest('hex');
if (sha !== '05fa24e9d475636bb77020e00a3c2b77a21516af63eef7baf6779ffc1f75e0c0') throw new Error('Original distribution checksum mismatch.');
const output = join(root, 'public/workshop-files');
await mkdir(output, {recursive:true});
const temp = await mkdtemp(join(tmpdir(), 'hollowdeep-kit-'));
const stage = join(temp, 'hollowdeep-server-kit');
await mkdir(stage);
const files = [];
async function include(source, path) {
  const text = await readFile(source, 'utf8');
  files.push({path, content:text, baseContent:text});
  await mkdir(dirname(join(stage, path)), {recursive:true});
  await copyFile(source, join(stage, path));
}
async function walk(path) {
  for (const item of await readdir(path, {withFileTypes:true})) {
    if (item.name.startsWith('.') || item.name === '__pycache__') continue;
    const full = join(path, item.name);
    if (item.isDirectory()) await walk(full);
    else if (item.isFile()) await include(full, relative(join(root, 'engine'), full));
  }
}
try {
  await walk(join(root, 'engine'));
  for (const name of ['index.mjs','protocol.mjs','package.json','package-lock.json']) await include(join(root,'server',name), 'bridge/'+name);
  await copyFile(archive, join(stage, 'Mordor_3.00.tar.gz'));
  await writeFile(join(output, 'index.json'), serializeProject({format:'hollowdeep-workshop',version:1,name:'Hollowdeep server kit',files}));
  execFileSync('tar', ['-czf',join(output,'hollowdeep-server-kit.tar.gz'),'-C',temp,'hollowdeep-server-kit'], {stdio:'inherit'});
  const bundle = await readFile(join(output,'hollowdeep-server-kit.tar.gz'));
  await writeFile(join(output,'hollowdeep-server-kit.sha256'), createHash('sha256').update(bundle).digest('hex')+'  hollowdeep-server-kit.tar.gz\n');
  console.log(`Packaged ${files.length} editable files and original distribution (${bundle.length} bytes).`);
} finally { await rm(temp, {recursive:true,force:true}); }
