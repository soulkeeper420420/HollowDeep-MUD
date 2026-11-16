"""Round 73G PRIVATE reward/save protocol. NOT a native item-grant implementation.

This module may be used only with a *trusted* engine-side bridge that durably
writes a claim receipt and all corresponding reward changes in the SAME atomic
player-save operation. The existing Mordor player serializer has no such bridge;
therefore this module MUST NOT be wired into live chest commands yet.
"""

import hashlib
import json
import sqlite3

MAX_ITEMS = 32
MAX_GOLD = 1000000


class DeliveryError(ValueError):
    pass


def _canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _item_identifier(claim_id, index, unit):
    return hashlib.sha256(f"HollowDeep:treasure:v1:{claim_id}:{index}:{unit}".encode("ascii")).hexdigest()[:32]


def _build_manifest(claim, trusted_templates):
    """Use only a server-authored native-template catalog, never a client list."""
    if type(claim) is not dict or not all(k in claim for k in ("claim_id", "owner_id", "rewards")):
        raise DeliveryError("Missing immutable ledger claim")
    claim_id, owner_id, rewards = (claim[k] for k in ("claim_id", "owner_id", "rewards"))
    if (type(claim_id) is not str or len(claim_id) != 32 or
            any(c not in "0123456789abcdef" for c in claim_id) or
            type(owner_id) is not str or not 3 <= len(owner_id) <= 79 or
            type(trusted_templates) is not dict or type(rewards) is not list or
            not 1 <= len(rewards) <= 8):
        raise DeliveryError("Invalid claim or trusted template catalog")
    gold, items = 0, []
    for index, row in enumerate(rewards):
        if type(row) is not dict or row.get("kind") not in ("gold", "item", "material"):
            raise DeliveryError("Unsupported reward")
        kind = row["kind"]
        if kind == "gold":
            if set(row) != {"kind", "amount"} or type(row["amount"]) is not int or not 1 <= row["amount"] <= MAX_GOLD:
                raise DeliveryError("Invalid gold reward")
            gold += row["amount"]
            if gold > MAX_GOLD:
                raise DeliveryError("Gold reward exceeds total cap")
            continue
        fields = ({"kind", "template_id", "quantity", "enchantment"} if kind == "item" else
                  {"kind", "template_id", "quantity"})
        tid, qty = row.get("template_id"), row.get("quantity")
        if (set(row) != fields or type(tid) is not int or type(qty) is not int or
                not 1 <= tid <= 999999 or not 1 <= qty <= MAX_ITEMS or
                len(items) + qty > MAX_ITEMS):
            raise DeliveryError("Invalid or oversized item reward")
        native = trusted_templates.get(tid)
        if type(native) is not dict or native.get("kind") != kind:
            raise DeliveryError("Unknown or incompatible native reward template")
        enchant = row.get("enchantment") if kind == "item" else None
        if enchant is not None:
            if (type(enchant) is not dict or set(enchant) != {"effect", "power"} or
                    type(enchant.get("effect")) is not str or type(enchant.get("power")) is not int or
                    type(native.get("enchant_caps")) is not dict or
                    type(native["enchant_caps"].get(enchant["effect"])) is not int or
                    not 1 <= enchant["power"] <= native["enchant_caps"][enchant["effect"]]):
                raise DeliveryError("Enchantment exceeds native template capabilities")
        for unit in range(qty):
            items.append({"instance_id": _item_identifier(claim_id, index, unit),
                          "template_id": tid, "kind": kind, "enchantment": enchant})
    return {"format": "HD-NATIVE-REWARD-V1", "claim_id": claim_id,
            "owner_id": owner_id, "gold": gold, "items": items}


def _digest(manifest):
    return hashlib.sha256(_canonical(manifest).encode("ascii")).hexdigest()


class DurableRewardCoordinator:
    """Ledger stays pending until a trusted native save proves atomic receipt.

    Required bridge contract:
      read_receipt(owner_id, claim_id) -> {claim_id, digest} or None;
      grant_and_save_atomically(owner_id, manifest, digest) -> None.
    The latter MUST persist the receipt with the items/gold in one transaction,
    deduplicate the claim inside that transaction, and persist before return.
    A separate receipt sidecar + original Mordor save is NOT atomic and unsafe.
    """

    def __init__(self, ledger, native_save_bridge):
        self.ledger = ledger
        self.bridge = native_save_bridge

    def _prepare(self, claim, templates):
        # Uses the SAME durable SQLite database as the claim ledger. Once
        # inserted, the manifest survives catalog changes and process crashes.
        with self.ledger.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS reward_manifests (
                claim_id TEXT PRIMARY KEY REFERENCES claims(claim_id),
                owner_id TEXT NOT NULL, manifest TEXT NOT NULL, digest TEXT NOT NULL
            )""")
            row = db.execute("SELECT owner_id,manifest,digest FROM reward_manifests WHERE claim_id=?",
                             (claim["claim_id"],)).fetchone()
            if row is not None:
                owner, body, digest = row
                try:
                    manifest = json.loads(body)
                except ValueError as exc:
                    raise DeliveryError("Corrupt persisted manifest") from exc
                if (owner != claim["owner_id"] or manifest.get("owner_id") != owner or
                        manifest.get("claim_id") != claim["claim_id"] or _digest(manifest) != digest):
                    raise DeliveryError("Persisted reward manifest mismatch")
                return manifest, digest
            manifest = _build_manifest(claim, templates)
            digest = _digest(manifest)
            db.execute("INSERT INTO reward_manifests VALUES(?,?,?,?)",
                       (claim["claim_id"], claim["owner_id"], _canonical(manifest), digest))
            return manifest, digest

    def deliver(self, instance_id, owner_id, trusted_carried_map_ids, trusted_native_templates):
        # Existing ledger authorizes the owner, actual held-map snapshot,
        # trusted guardian deaths, and returns a stable one-time claim ID.
        claim = self.ledger.claim(instance_id, owner_id, trusted_carried_map_ids)
        manifest, digest = self._prepare(claim, trusted_native_templates)
        expected = {"claim_id": claim["claim_id"], "digest": digest}
        receipt = self.bridge.read_receipt(owner_id, claim["claim_id"])
        if receipt is None:
            # This method must be atomic and idempotent. A crash inside is safe
            # only when player item changes and receipt share one commit.
            self.bridge.grant_and_save_atomically(owner_id, manifest, digest)
            receipt = self.bridge.read_receipt(owner_id, claim["claim_id"])
        if type(receipt) is not dict or receipt != expected:
            raise DeliveryError("Trusted native player save lacks matching claim receipt")
        recorded = self.ledger.acknowledge_native_delivery(
            claim["claim_id"], owner_id, "native." + digest[:32])
        return {"claim": recorded, "manifest_digest": digest, "items": len(manifest["items"]),
                "gold": manifest["gold"]}