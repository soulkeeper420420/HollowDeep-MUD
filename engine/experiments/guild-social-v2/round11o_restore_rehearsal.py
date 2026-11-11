"""Restore an existing native-updater backup into a new private directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import stat
import tarfile
import tempfile


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path)
    parser.add_argument("updater", type=Path)
    args = parser.parse_args()
    backup = args.backup.resolve(strict=True)
    live = Path("/srv/hollowdeep")
    if (backup.name != "backup" or backup.parent.parent != live / ".updates"
            or not backup.parent.name.startswith("native-")):
        raise SystemExit("Expected a native updater backup")
    work = Path(tempfile.mkdtemp(prefix="round11o-restore-",
                                 dir="/root/hollowdeep-dev"))
    print("Private restore directory:", work, flush=True)
    isolated = work / "isolated"
    isolated.mkdir(mode=0o700)
    archive_path = backup / "world.tar.gz"
    manifest_path = backup / "files.json"
    archive_hash = digest(archive_path)
    manifest_hash = digest(manifest_path)
    originals = json.loads(manifest_path.read_text())
    remapped = {}
    backup_hashes = {}
    for name, metadata in originals.items():
        source = Path(name)
        relative = source.relative_to(live)
        if ".." in relative.parts or relative.parts[:1] not in (("kit",), ("world",)):
            raise ValueError("Unsafe rollback target")
        target = isolated / relative
        if metadata is not None:
            filename = metadata["file"]
            if not re.fullmatch(r"file-[0-9]+", filename):
                raise ValueError("Unsafe rollback backup filename")
            content = backup / filename
            if content.is_symlink() or digest(content) != metadata["sha256"]:
                raise ValueError("Rollback payload checksum mismatch")
            backup_hashes[content] = metadata["sha256"]
        remapped[str(target)] = metadata

    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        names = set()
        for member in members:
            path = Path(member.name)
            if (path.parts[:1] != ("world",) or ".." in path.parts or
                    path in names or not (member.isfile() or member.isdir())):
                raise ValueError("Unexpected archive entry")
            names.add(path)
        archive.extractall(isolated, members=members, filter="data")
        count = 0
        for member in members:
            if member.isfile():
                with archive.extractfile(member) as stream:
                    expected = hashlib.file_digest(stream, "sha256").hexdigest()
                if digest(isolated / member.name) != expected:
                    raise ValueError("Restored archive member checksum mismatch")
                count += 1
    print("Archived world files restored and verified:", count, flush=True)

    for name, metadata in remapped.items():
        target = Path(name)
        if target.is_relative_to(isolated / "world"):
            if metadata is None and target.exists():
                raise ValueError("Archive unexpectedly contains an added target")
            if metadata is not None and digest(target) != metadata["sha256"]:
                raise ValueError("Archive and rollback manifest disagree")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"Round 11O simulated replacement\n")

    restore_files = runpy.run_path(str(args.updater.resolve(strict=True)))["restore_files"]
    restore_files(backup.parent, remapped)
    for name, metadata in remapped.items():
        target = Path(name)
        if metadata is None:
            if target.exists():
                raise ValueError("Rollback did not remove a simulated new file")
            continue
        st = target.stat()
        if (digest(target) != metadata["sha256"] or stat.S_IMODE(st.st_mode) != metadata["mode"]
                or st.st_uid != metadata["uid"] or st.st_gid != metadata["gid"]):
            raise ValueError("Restored target checksum or metadata mismatch")
    print("Rollback targets verified:", len(remapped), flush=True)
    for path, expected in {archive_path: archive_hash, manifest_path: manifest_hash,
                           **backup_hashes}.items():
        if digest(path) != expected:
            raise ValueError("Original backup changed")
    print("Original backup checksums verified", flush=True)


if __name__ == "__main__":
    if os.geteuid() != 0:
        raise SystemExit("Root is required to verify original numeric ownership")
    main()
