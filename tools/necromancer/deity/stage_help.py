#!/usr/bin/env python3
"""Install packaged native help into an isolated world, never a live tree."""
from pathlib import Path
import sys, os
NAMES = ('help.150', 'help.151', 'necromancer', 'deity', 'corpses-pending')

def main():
    if len(sys.argv) != 2: raise SystemExit('Usage: stage_help.py PRIVATE_WORLD')
    raw=Path(sys.argv[1]); world=raw.resolve(strict=True)
    if raw.is_symlink() or not world.is_dir() or not any(x.startswith(('necromancer-playtest-', 'necro-socket-run-')) for x in world.parts) or not str(world).startswith(('/root/hollowdeep-dev/', '/mnt/data/')):
        raise SystemExit('Refusing non-disposable help destination')
    dest=world/'help'; pkg=Path(__file__).resolve().parent/'help'
    if dest.is_symlink() or (dest.exists() and not dest.is_dir()): raise SystemExit('Invalid help directory')
    data={n:(pkg/n).read_bytes() for n in NAMES}
    for n, b in data.items():
        p=dest/n
        if p.is_symlink() or (p.exists() and (not p.is_file() or p.read_bytes()!=b)):
            raise SystemExit('Existing different help page: '+n+'; no help changed')
    dest.mkdir(mode=0o755, exist_ok=True)
    for n,b in data.items():
        p=dest/n
        if p.exists(): continue
        with p.open('xb') as f: f.write(b)
        os.chmod(p,0o644)
    print('DEITY: five native help files installed in private world: '+str(dest))
if __name__ == '__main__': main()
