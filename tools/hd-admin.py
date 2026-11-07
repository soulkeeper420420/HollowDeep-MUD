#!/usr/bin/env python3
"""HollowDeep private audit management. Run as root on the VPS."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

DATA = Path("/var/lib/hollowdeep/investigation-reviews")
BACKUPS = Path("/root/hd-audit-backups")
FILES = ("statuses.json", "history.jsonl", "statuses.lock")

def regular(path):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("Missing or unsafe file: " + str(path))
    return path

def validate():
    if DATA.is_symlink() or not DATA.is_dir():
        raise RuntimeError("Unsafe audit directory")
    status = json.loads(regular(DATA / FILES[0]).read_text())
    if not isinstance(status, dict):
        raise RuntimeError("Status JSON is not an object")
    count = 0
    with regular(DATA / FILES[1]).open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                if not isinstance(json.loads(line), dict):
                    raise RuntimeError(f"Audit line {n} is not an object")
                count += 1
    return len(status), count

def status():
    findings, count = validate()
    paths = [(DATA, 0o700)] + [(DATA / f, 0o600) for f in FILES]
    issues = []
    for path, expected in paths:
        if path.is_symlink():
            raise RuntimeError("Unsafe symlink: " + str(path))
        actual = path.stat().st_mode & 0o777
        if actual != expected:
            issues.append(f"{path.name}: {actual:03o} (expected {expected:03o})")
    if len({p.stat().st_uid for p, _ in paths}) != 1 or len({p.stat().st_gid for p, _ in paths}) != 1:
        issues.append("Review files and directory have differing owners")
    try:
        active = subprocess.run(["systemctl", "is-active", "cron"], capture_output=True, text=True, timeout=8).stdout.strip() == "active"
    except (OSError, subprocess.TimeoutExpired):
        active = False
    try:
        lines = Path("/etc/cron.d/hd-audit-health").read_text().splitlines()
        configured = any(x.strip().startswith("0 * * * * root /usr/local/bin/hd-audit-alert") for x in lines)
    except OSError:
        configured = False
    print(f"Audit JSON OK | saved findings: {findings} | events: {count}")
    print("Permissions:", "OK" if not issues else "; ".join(issues))
    print("Cron service:", "active" if active else "not confirmed")
    print("Hourly alert:", "configured" if configured else "not confirmed")
    print("Checks syntax and settings, not whether scheduled execution occurred.")
    return 0 if not issues and active and configured else 1

def backup():
    validate()
    if BACKUPS.is_symlink():
        raise RuntimeError("Unsafe backup directory")
    BACKUPS.mkdir(parents=True, exist_ok=True, mode=0o700)
    BACKUPS.chmod(0o700)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = BACKUPS / f"audit-{stamp}-{os.getpid()}.tgz"
    temp = BACKUPS / ("." + dest.name + ".partial")
    with regular(DATA / "statuses.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            validate()
            with temp.open("xb") as output:
                os.fchmod(output.fileno(), 0o600)
                with tarfile.open(fileobj=output, mode="w:gz") as archive:
                    for name in FILES:
                        archive.add(regular(DATA / name), arcname="investigation-reviews/" + name, recursive=False)
            with tarfile.open(temp, "r:gz") as archive:
                expected = {"investigation-reviews/" + n for n in FILES}
                if set(archive.getnames()) != expected:
                    raise RuntimeError("Archive entries do not match expected files")
                fileobj = archive.extractfile("investigation-reviews/statuses.json")
                if fileobj is None or not isinstance(json.load(fileobj), dict):
                    raise RuntimeError("Archived status JSON invalid")
            temp.rename(dest)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            if temp.exists():
                temp.unlink()
    print(f"PRIVATE BACKUP OK: {dest} ({dest.stat().st_size} bytes)")
    print("No live files were restored or changed.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="HollowDeep website audit tools; not MUD management")
    parser.add_argument("command", nargs="?", choices=["status", "backup"], default="status")
    args = parser.parse_args()
    if os.geteuid():
        parser.error("Run as root with sudo")
    try:
        return backup() if args.command == "backup" else status()
    except (OSError, ValueError, RuntimeError, tarfile.TarError) as exc:
        print("HOLLOWDEEP CHECK FAILED: " + str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
