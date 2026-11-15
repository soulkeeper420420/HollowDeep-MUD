"""Round 73 pure Python unit tests; NOT a native-engine gameplay replay."""

import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from claim_ledger import TreasureLedger, TreasureError, GuardiansRemain, MapNotHeld
from treasure_sites import assets, validate


def expected_error(fn, message):
    try:
        fn()
    except (TreasureError, ValueError) as exc:
        assert message.lower() in str(exc).lower(), (message, exc)
    else:
        raise AssertionError("Expected rejection: " + message)


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.plan = {"rooms": [
            {"room_id": 14},
            {"room_id": 10001, "wilderness": {"region": "Copperreach", "x": 1, "y": 1, "terrain": "road", "landmark": "Cairn"}},
            {"room_id": 10002, "wilderness": {"region": "Copperreach", "x": 2, "y": 1, "terrain": "forest", "landmark": ""}},
        ], "treasure_sites": [
            {"site_id": "copper-cache", "room_id": 10002,
             "guardians": [7, 9], "chest_label": "Copperbound Chest",
             "tier": "rare", "clue": "Beyond the cairn, seek the eastern shadow."}
        ]}

    def test_metadata_and_determinism(self):
        data = assets(self.plan, {7, 9})["rooms/treasure_sites.json"]
        self.assertEqual(data, assets(copy.deepcopy(self.plan), {7, 9})["rooms/treasure_sites.json"])
        payload = json.loads(data)
        self.assertEqual(payload["format"], "HD-TREASURE-BLUEPRINT-V1")
        self.assertEqual(payload["sites"][0]["column"], 2)
        self.assertEqual(payload["sites"][0]["guardians"], [7, 9])
        self.assertEqual(assets({"rooms": []}, {7}), {})

    def test_invalid_sites_rejected_atomically(self):
        for field, bad, phrase in [
            ("room_id", 14, "mapped wilderness"),
            ("room_id", 15999, "mapped wilderness"),
            ("guardians", [], "templates"),
            ("guardians", [7, 7], "templates"),
            ("guardians", [7, 12345], "templates"),
            ("tier", "mythic", "rarity"),
            ("site_id", "../unsafe", "site ID"),
            ("chest_label", "<b>loot</b>", "chest label"),
            ("clue", "bad\nclue", "clue"),
        ]:
            with self.subTest(field=field, bad=bad):
                changed = copy.deepcopy(self.plan)
                changed["treasure_sites"][0][field] = bad
                expected_error(lambda: validate(changed, {7, 9}), phrase)
        duplicate = copy.deepcopy(self.plan)
        duplicate["treasure_sites"].append(copy.deepcopy(duplicate["treasure_sites"][0]))
        expected_error(lambda: validate(duplicate, {7, 9}), "duplicate")
        self.assertEqual(len(self.plan["treasure_sites"]), 1)


class ClaimTests(unittest.TestCase):
    def setUp(self):
        self.dir = TemporaryDirectory(prefix="hd-round73-")
        self.addCleanup(self.dir.cleanup)
        self.db_path = Path(self.dir.name) / "claims.sqlite3"
        self.ledger = TreasureLedger(self.db_path)
        self.rewards = [{"kind": "item", "template_id": 101, "quantity": 1,
                         "enchantment": {"effect": "frost_resist", "power": 17}},
                        {"kind": "gold", "amount": 850}]
        self.ledger.register("inst.0001", "map.0001", "player.01", 10002,
                             ["guardian.1", "guardian.2"], self.rewards, clue="Beyond the cairn, seek the eastern shadow.")

    def test_early_claim_denied_and_owner_bound(self):
        expected_error(lambda: self.ledger.claim("inst.0001", "player.01", ["map.0001"]), "guardians")
        self.assertFalse(self.ledger.record_verified_kill("inst.0001", "guardian.1", "event.1", "player.01"))
        expected_error(lambda: self.ledger.claim("inst.0001", "player.02", ["map.0001"]), "another player")
        expected_error(lambda: self.ledger.claim("inst.0001", "player.01", ["map.0001"]), "guardians")
        self.assertTrue(self.ledger.record_verified_kill("inst.0001", "guardian.2", "event.2", "player.01"))
        self.assertEqual(self.ledger.claim("inst.0001", "player.01", ["map.0001"])["rewards"], self.rewards)

    def test_kill_replay_wrong_instance_and_duplicate_map(self):
        self.assertFalse(self.ledger.record_verified_kill("inst.0001", "guardian.1", "event.1", "player.01"))
        self.assertFalse(self.ledger.record_verified_kill("inst.0001", "guardian.1", "event.1", "player.01"))
        expected_error(lambda: self.ledger.record_verified_kill("inst.0001", "guardian.2", "event.1", "player.01"), "event ID reused")
        expected_error(lambda: self.ledger.record_verified_kill("inst.0001", "guardian.other", "event.3", "player.01"), "does not belong")
        expected_error(lambda: self.ledger.record_verified_kill("inst.0001", "guardian.1", "event.4", "player.01"), "already defeated")
        expected_error(lambda: self.ledger.register("inst.0002", "map.0001", "player.01", 10002,
                                                     ["guardian.3"], self.rewards), "already been activated")
        self.assertEqual(self.ledger.register("inst.0001", "map.0001", "player.01", 10002,
                                               ["guardian.1", "guardian.2"], self.rewards, clue="Beyond the cairn, seek the eastern shadow."), "inst.0001")
        expected_error(lambda: self.ledger.register("inst.0001", "map.0001", "player.01", 10002,
                                                     ["guardian.1"], self.rewards), "reused")

    def test_concurrent_claims_same_claim_id(self):
        for index in (1, 2):
            self.ledger.record_verified_kill("inst.0001", f"guardian.{index}", f"event.{index}", "player.01")
        with ThreadPoolExecutor(max_workers=8) as workers:
            claims = list(workers.map(lambda _: self.ledger.claim("inst.0001", "player.01", ["map.0001"]), range(20)))
        self.assertEqual(len({row["claim_id"] for row in claims}), 1)
        self.assertEqual({row["delivery_state"] for row in claims}, {"pending"})
        self.assertEqual(claims[0]["rewards"], self.rewards)

    def test_restart_pending_and_ack_idempotency(self):
        for index in (1, 2):
            self.ledger.record_verified_kill("inst.0001", f"guardian.{index}", f"event.{index}", "player.01")
        pending = self.ledger.claim("inst.0001", "player.01", ["map.0001"])
        resumed = TreasureLedger(self.db_path)
        self.assertEqual(resumed.claim("inst.0001", "player.01", ["map.0001"]), pending)
        delivered = resumed.acknowledge_native_delivery(pending["claim_id"], "player.01", "native-receipt.01")
        self.assertEqual(delivered["delivery_state"], "delivered")
        self.assertEqual(self.ledger.claim("inst.0001", "player.01", ["map.0001"]), delivered)
        self.assertEqual(resumed.acknowledge_native_delivery(pending["claim_id"], "player.01", "native-receipt.01"), delivered)
        expected_error(lambda: resumed.acknowledge_native_delivery(pending["claim_id"], "player.01", "native-receipt.02"), "conflicting receipt")
        expected_error(lambda: resumed.acknowledge_native_delivery(pending["claim_id"], "player.02", "native-receipt.01"), "unknown claim")

    def test_locate_requires_physical_map_and_owner(self):
        clue = "Beyond the cairn, seek the eastern shadow."
        expected_error(lambda: self.ledger.locate("player.01", []), "carry")
        expected_error(lambda: self.ledger.locate("player.01", ["map.other"]), "carry")
        expected_error(lambda: self.ledger.locate("player.02", ["map.0001"]), "carry")
        expected_error(lambda: self.ledger.locate("player.01", ["map.other"], "map.0001"), "matching")
        info = self.ledger.locate("player.01", ["map.0001"])
        self.assertEqual(info, {"map_id": "map.0001", "clue": clue})
        self.assertEqual(self.ledger.locate("player.01", ["map.0001"], "map.0001"), info)
        self.assertNotIn("room_id", info)
        self.assertNotIn("coordinates", info)
        expected_error(lambda: self.ledger.locate("player.01", []), "carry")
        self.assertEqual(self.ledger.locate("player.01", ["map.0001"]), info)

    def test_claim_denied_after_dropping_map_even_with_guardians_defeated(self):
        for index in (1, 2):
            self.ledger.record_verified_kill("inst.0001", f"guardian.{index}", f"event.{index}", "player.01")
        expected_error(lambda: self.ledger.claim("inst.0001", "player.01"), "trusted")
        expected_error(lambda: self.ledger.claim("inst.0001", "player.01", []), "matching")
        expected_error(lambda: self.ledger.claim("inst.0001", "player.01", ["map.other"]), "matching")
        claim = self.ledger.claim("inst.0001", "player.01", ["map.0001"])
        expected_error(lambda: self.ledger.claim("inst.0001", "player.01", []), "matching")
        self.assertEqual(self.ledger.claim("inst.0001", "player.01", ["map.0001"]), claim)

    def test_locate_requires_map_selection_if_multiple_are_carried(self):
        self.ledger.register("inst.0002", "map.0002", "player.01", 10003,
                             ["guardian.3"], self.rewards, clue="Follow the river bend.")
        expected_error(lambda: self.ledger.locate("player.01", ["map.0001", "map.0002"]), "multiple")
        self.assertEqual(self.ledger.locate("player.01", ["map.0002", "map.0001"], "map.0002"),
                         {"map_id": "map.0002", "clue": "Follow the river bend."})
        expected_error(lambda: self.ledger.locate("player.01", "map.0001"), "snapshot")
        expected_error(lambda: self.ledger.locate("player.01", ["../map"]), "carried map ID")
        expected_error(lambda: self.ledger.locate("player.01", ["map.0001"] * 101), "snapshot")

    def test_clue_registration_is_immutable_and_safe(self):
        expected_error(lambda: self.ledger.register("inst.0001", "map.0001", "player.01", 10002,
                            ["guardian.1", "guardian.2"], self.rewards, clue="Different clue."),
                       "clue changed")
        for bad in ("Bad\nclue", "<script>", "a" * 181, " leading space", "", None):
            if bad is None:
                # Existing activated clue cannot be erased by retry.
                expected_error(lambda: self.ledger.register("inst.0001", "map.0001", "player.01", 10002,
                                ["guardian.1", "guardian.2"], self.rewards), "clue changed")
            else:
                expected_error(lambda: self.ledger.register("inst.0003", "map.0003", "player.01", 10004,
                                ["guardian.3"], self.rewards, clue=bad), "clue")
        resumed = TreasureLedger(self.db_path)
        self.assertEqual(resumed.locate("player.01", ["map.0001"])["map_id"], "map.0001")

    def test_invalid_reward_snapshot_rejected(self):
        bad_rewards = [
            [{"kind": "gold", "amount": True}],
            [{"kind": "item", "template_id": 5, "quantity": 1,
              "enchantment": {"effect": "admin_access", "power": 100}}],
            [{"kind": "material", "template_id": -1, "quantity": 1}],
        ]
        for index, bad in enumerate(bad_rewards):
            with self.subTest(index=index):
                expected_error(lambda: self.ledger.register("inst.new"+str(index), "map.new"+str(index),
                                                              "player.01", 10003, ["guardian.3"], bad),
                               "invalid")
        self.assertFalse((self.db_path.parent / "unexpected").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
