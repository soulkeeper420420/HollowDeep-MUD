"""Offline Round 73G crash/replay model; NOT a native gameplay verification."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from claim_ledger import TreasureLedger
from durable_delivery import DurableRewardCoordinator, DeliveryError, _build_manifest


CATALOG = {
    101: {"kind": "item", "enchant_caps": {"frost_resist": 20, "strength": 3}},
    102: {"kind": "material"},
}
REWARDS = [
    {"kind": "item", "template_id": 101, "quantity": 1,
     "enchantment": {"effect": "frost_resist", "power": 17}},
    {"kind": "gold", "amount": 850},
    {"kind": "material", "template_id": 102, "quantity": 2},
]


class SimulatedAtomicNativeSave:
    """Private test double. NOT suitable for the real legacy native engine."""
    def __init__(self, path):
        self.path = str(path)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS player (owner TEXT PRIMARY KEY, gold INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS item (
                    instance_id TEXT PRIMARY KEY, owner TEXT NOT NULL,
                    template_id INTEGER NOT NULL, effect TEXT, power INTEGER
                );
                CREATE TABLE IF NOT EXISTS receipt (
                    owner TEXT NOT NULL, claim_id TEXT NOT NULL, digest TEXT NOT NULL,
                    PRIMARY KEY (owner, claim_id)
                );
            """)
        self.fail_next = None

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        try:
            yield db
        finally:
            db.close()

    def read_receipt(self, owner, claim):
        with self.connection() as db:
            row = db.execute("SELECT digest FROM receipt WHERE owner=? AND claim_id=?",
                             (owner, claim)).fetchone()
            return {"claim_id": claim, "digest": row[0]} if row else None

    def grant_and_save_atomically(self, owner, manifest, digest):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            claim = manifest["claim_id"]
            old = db.execute("SELECT digest FROM receipt WHERE owner=? AND claim_id=?",
                             (owner, claim)).fetchone()
            if old:
                if old[0] != digest:
                    raise DeliveryError("Conflicting persisted claim")
                db.execute("COMMIT")
                return
            if self.fail_next == "before_commit":
                self.fail_next = None
                raise RuntimeError("Simulated crash before atomic player save")
            db.execute("INSERT OR IGNORE INTO player VALUES(?,0)", (owner,))
            db.execute("UPDATE player SET gold=gold+? WHERE owner=?", (manifest["gold"], owner))
            for item in manifest["items"]:
                enchant = item["enchantment"]
                db.execute("INSERT INTO item VALUES(?,?,?,?,?)",
                           (item["instance_id"], owner, item["template_id"],
                            enchant["effect"] if enchant else None,
                            enchant["power"] if enchant else None))
            db.execute("INSERT INTO receipt VALUES(?,?,?)", (owner, claim, digest))
            db.execute("COMMIT")
        if self.fail_next == "after_commit":
            self.fail_next = None
            raise RuntimeError("Simulated crash after atomic save, before acknowledgment")

    def totals(self, owner):
        with self.connection() as db:
            gold = db.execute("SELECT gold FROM player WHERE owner=?", (owner,)).fetchone()
            items = db.execute("SELECT instance_id FROM item WHERE owner=? ORDER BY instance_id",
                               (owner,)).fetchall()
            receipts = db.execute("SELECT count(*) FROM receipt WHERE owner=?", (owner,)).fetchone()[0]
            return ((gold[0] if gold else 0), tuple(x[0] for x in items), receipts)


class Tests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory(prefix="hd-73g-test-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.ledger = TreasureLedger(self.root / "ledger.sqlite3")
        self.ledger.register("encounter.001", "map.001", "player.01", 10001,
                             ["guardian.01", "guardian.02"], REWARDS,
                             clue="Seek the ancient cairn.")
        self.native = SimulatedAtomicNativeSave(self.root / "native-save-simulation.sqlite3")
        self.coord = DurableRewardCoordinator(self.ledger, self.native)

    def defeat(self):
        self.ledger.record_verified_kill("encounter.001", "guardian.01", "event.001", "player.01")
        self.ledger.record_verified_kill("encounter.001", "guardian.02", "event.002", "player.01")

    def deliver(self, *, owner="player.01", held=None, catalog=None):
        return self.coord.deliver("encounter.001", owner,
                                  ["map.001"] if held is None else held,
                                  CATALOG if catalog is None else catalog)

    def test_no_early_reward_wrong_owner_or_dropped_map(self):
        with self.assertRaises(ValueError): self.deliver()
        self.defeat()
        with self.assertRaises(ValueError): self.deliver(owner="player.02")
        with self.assertRaises(ValueError): self.deliver(held=[])
        self.assertEqual(self.native.totals("player.01"), (0, (), 0))

    def test_single_delivery_and_idempotent_reopen(self):
        self.defeat()
        result = self.deliver()
        self.assertEqual(result["gold"], 850)
        self.assertEqual(result["items"], 3)
        expected = self.native.totals("player.01")
        self.assertEqual((expected[0], len(expected[1]), expected[2]), (850, 3, 1))
        self.assertEqual(self.deliver()["manifest_digest"], result["manifest_digest"])
        self.assertEqual(self.native.totals("player.01"), expected)
        with self.assertRaises(ValueError): self.deliver(held=[])

    def test_crash_before_native_save_retries_once(self):
        self.defeat()
        self.native.fail_next = "before_commit"
        with self.assertRaisesRegex(RuntimeError, "before atomic"): self.deliver()
        self.assertEqual(self.native.totals("player.01"), (0, (), 0))
        self.assertEqual(self.deliver()["gold"], 850)
        self.assertEqual(self.native.totals("player.01")[2], 1)

    def test_crash_after_native_save_before_ledger_ack(self):
        self.defeat()
        self.native.fail_next = "after_commit"
        with self.assertRaisesRegex(RuntimeError, "after atomic"): self.deliver()
        saved = self.native.totals("player.01")
        self.assertEqual(saved[0], 850)
        self.assertEqual(len(saved[1]), 3)
        self.assertEqual(self.ledger.claim("encounter.001", "player.01", ["map.001"])["delivery_state"], "pending")
        resumed = DurableRewardCoordinator(TreasureLedger(self.root / "ledger.sqlite3"),
                                           SimulatedAtomicNativeSave(self.root / "native-save-simulation.sqlite3"))
        self.assertEqual(resumed.deliver("encounter.001", "player.01", ["map.001"], CATALOG)["claim"]["delivery_state"], "delivered")
        self.assertEqual(self.native.totals("player.01"), saved)

    def test_catalog_changes_dont_mutate_prepared_manifest(self):
        self.defeat()
        self.native.fail_next = "before_commit"
        with self.assertRaises(RuntimeError): self.deliver()
        self.assertEqual(self.deliver(catalog={})["items"], 3)  # immutable preparation
        self.assertEqual(self.native.totals("player.01")[0], 850)

    def test_missing_template_or_invalid_enchantment_fails_closed(self):
        self.defeat()
        with self.assertRaisesRegex(DeliveryError, "native reward template"):
            self.deliver(catalog={})
        with self.assertRaisesRegex(DeliveryError, "Enchantment exceeds"):
            self.deliver(catalog={101: {"kind": "item", "enchant_caps": {"frost_resist": 5}},
                                  102: {"kind": "material"}})
        self.assertEqual(self.native.totals("player.01"), (0, (), 0))

    def test_malformed_reward_amount_and_bool_rejected(self):
        claim = {"claim_id": "a" * 32, "owner_id": "player.01",
                 "rewards": [{"kind": "gold", "amount": 900000},
                             {"kind": "gold", "amount": 900000}]}
        with self.assertRaisesRegex(DeliveryError, "total cap"):
            _build_manifest(claim, CATALOG)
        claim["rewards"] = [{"kind": "gold", "amount": True}]
        with self.assertRaisesRegex(DeliveryError, "Invalid gold"):
            _build_manifest(claim, CATALOG)
        claim["rewards"] = [{"kind": "item", "template_id": 101, "quantity": 33,
                             "enchantment": None}]
        with self.assertRaisesRegex(DeliveryError, "oversized"):
            _build_manifest(claim, CATALOG)

    def test_forged_or_corrupt_native_receipt_not_acknowledged(self):
        self.defeat()
        with self.native.connection() as db:
            db.execute("INSERT INTO receipt VALUES(?,?,?)", ("player.01", "f" * 32, "wrong-digest"))
        # Need actual claim ID; reserve it without delivery.
        claim = self.ledger.claim("encounter.001", "player.01", ["map.001"])
        with self.native.connection() as db:
            db.execute("INSERT INTO receipt VALUES(?,?,?)", ("player.01", claim["claim_id"], "wrong-digest"))
        with self.assertRaisesRegex(DeliveryError, "lacks matching"):
            self.deliver()
        self.assertEqual(self.ledger.claim("encounter.001", "player.01", ["map.001"])["delivery_state"], "pending")

    def test_concurrent_replays_award_only_once(self):
        self.defeat()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.deliver(), range(16)))
        self.assertEqual(len(set(r["manifest_digest"] for r in results)), 1)
        self.assertEqual(self.native.totals("player.01")[0], 850)
        self.assertEqual(len(self.native.totals("player.01")[1]), 3)
        self.assertEqual(self.native.totals("player.01")[2], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)