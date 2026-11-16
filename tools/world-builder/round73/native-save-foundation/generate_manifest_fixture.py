#!/usr/bin/env python3
"""OFFLINE ONLY: produce C test constants from REAL ledger authorization.

Never emits player saves, secret keys, SQLite files, or production metadata.
Only for a disposable fixture; not a bridge a MUD player can invoke.
"""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from claim_ledger import TreasureLedger, GuardiansRemain, MapNotHeld
from durable_delivery import DurableRewardCoordinator


def main(output):
    catalog = {123: {"kind": "item", "enchant_caps": {}},
               124: {"kind": "material"}}
    rewards = [
        {"kind": "item", "template_id": 123, "quantity": 1, "enchantment": None},
        {"kind": "material", "template_id": 124, "quantity": 1},
        {"kind": "gold", "amount": 150},
    ]
    with TemporaryDirectory(prefix="hd-ledger-reward-") as root:
        ledger = TreasureLedger(Path(root) / "claim.sqlite3")
        ledger.register("encounter.nativeqa", "map.nativeqa", "Nativeqa", 10001,
                        ["guardian.nativeqa"], rewards, clue="Seek the cairn.")
        try:
            ledger.claim("encounter.nativeqa", "Nativeqa", ["map.nativeqa"])
        except GuardiansRemain:
            pass
        else:
            raise AssertionError("Early claim unexpectedly permitted")
        ledger.record_verified_kill("encounter.nativeqa", "guardian.nativeqa",
                                    "native.event.0001", "Nativeqa")
        try:
            ledger.claim("encounter.nativeqa", "Nativeqa", [])
        except MapNotHeld:
            pass
        else:
            raise AssertionError("Unheld map unexpectedly permitted")
        claim = ledger.claim("encounter.nativeqa", "Nativeqa", ["map.nativeqa"])
        coord = DurableRewardCoordinator(ledger, object())
        manifest, digest = coord._prepare(claim, catalog)
        assert manifest["owner_id"] == "Nativeqa" and manifest["gold"] == 150
        assert len(manifest["items"]) == 2
        assert manifest["items"][0]["template_id"] == 123
        assert manifest["items"][1]["template_id"] == 124
        assert all(x["enchantment"] is None for x in manifest["items"])
        # Test repeat lookups preserve a stable receipt and manifest snapshot.
        assert coord._prepare(ledger.claim("encounter.nativeqa", "Nativeqa", ["map.nativeqa"]), catalog) == (manifest, digest)
        keys = {
            "HD_FIX_CLAIM_ID": claim["claim_id"],
            "HD_FIX_DIGEST": digest,
            "HD_FIX_ITEM0": manifest["items"][0]["instance_id"],
            "HD_FIX_ITEM1": manifest["items"][1]["instance_id"],
        }
        lines = ["/* Generated test-only from trusted SQLite ledger, NOT production. */"]
        for k, v in keys.items():
            lines.append(f"#define {k} {json.dumps(v)}")
        Path(output).write_text("\n".join(lines) + "\n", encoding="ascii")
        print("ROUND 73G: trusted ledger guardian/map/immutable manifest fixture PASS")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: generate_manifest_fixture.py TEMP_HEADER")
    main(sys.argv[1])
