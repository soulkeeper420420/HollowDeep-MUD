"""SQLite-backed Round 73 guardian/claim state machine (private prototype).

The native engine must ONLY call this from trusted combat and inventory hooks.
This module is not network-exposed. A claim is a pending delivery instruction;
it must not award an item until native inventory persistence supports the same
claim ID idempotently. It does not itself grant or save in-game items.
"""

from contextlib import contextmanager
import json
from pathlib import Path
import re
import secrets
import sqlite3

TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{2,95}\Z")
MAX_REWARD = 8
CLUE = re.compile(r"[A-Za-z0-9 .,;:'!?()/-]{1,180}\Z")
MAX_CARRIED_MAPS = 100


class TreasureError(ValueError):
    pass


class GuardiansRemain(TreasureError):
    pass


class MapNotHeld(TreasureError):
    pass


def check_token(value, label):
    if type(value) is not str or not TOKEN.fullmatch(value):
        raise TreasureError("Invalid " + label)
    return value


def checked_inventory_map_ids(carried_map_ids):
    """Accept only IDs reported by a *trusted native inventory traversal*.

    Never populate this parameter from player-provided command arguments or a
    browser JSON request. Map instance IDs must be unique in native storage.
    """
    if type(carried_map_ids) not in (list, tuple, set, frozenset) or \
            len(carried_map_ids) > MAX_CARRIED_MAPS:
        raise TreasureError("Invalid trusted carried-map snapshot")
    for item in carried_map_ids:
        check_token(item, "carried map ID")
    return frozenset(carried_map_ids)


def canonical_clue(clue):
    if type(clue) is not str or not CLUE.fullmatch(clue) or clue != clue.strip():
        raise TreasureError("Invalid treasure clue")
    return clue


def canonical_reward(rewards):
    """Validate *server-selected* reward snapshot before it can be claimed."""
    if not isinstance(rewards, list) or not 1 <= len(rewards) <= MAX_REWARD:
        raise TreasureError("Invalid reward count")
    for row in rewards:
        if type(row) is not dict or row.get("kind") not in ("gold", "item", "material"):
            raise TreasureError("Invalid reward kind")
        kind = row["kind"]
        fields = ({"kind", "amount"} if kind == "gold" else
                  {"kind", "template_id", "quantity", "enchantment"} if kind == "item" else
                  {"kind", "template_id", "quantity"})
        if set(row) != fields:
            raise TreasureError("Unexpected reward fields")
        if kind == "gold":
            if type(row["amount"]) is not int or not 1 <= row["amount"] <= 1000000:
                raise TreasureError("Invalid gold amount")
        else:
            if type(row["template_id"]) is not int or not 1 <= row["template_id"] <= 999999 or \
               type(row["quantity"]) is not int or not 1 <= row["quantity"] <= 99:
                raise TreasureError("Invalid reward template or quantity")
        if kind == "item":
            enchant = row["enchantment"]
            if enchant is not None and (type(enchant) is not dict or
                set(enchant) != {"effect", "power"} or
                enchant.get("effect") not in ("strength", "spellpower", "frost_resist", "fire_damage", "regeneration") or
                type(enchant.get("power")) is not int or not 1 <= enchant["power"] <= 100):
                raise TreasureError("Invalid enchantment")
    return json.dumps(rewards, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class TreasureLedger:
    def __init__(self, database):
        self.database = Path(database)
        if self.database.exists() and self.database.is_symlink():
            raise TreasureError("Refusing symlink database")
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            schema = """
                CREATE TABLE IF NOT EXISTS encounters (
                  instance_id TEXT PRIMARY KEY, map_id TEXT NOT NULL UNIQUE,
                  owner_id TEXT NOT NULL, room_id INTEGER NOT NULL,
                  guardians TEXT NOT NULL, reward_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS map_clues (
                  instance_id TEXT PRIMARY KEY, clue TEXT NOT NULL,
                  FOREIGN KEY(instance_id) REFERENCES encounters(instance_id)
                );
                CREATE TABLE IF NOT EXISTS defeats (
                  instance_id TEXT NOT NULL, guardian_id TEXT NOT NULL,
                  combat_event_id TEXT NOT NULL UNIQUE, killer_id TEXT NOT NULL,
                  PRIMARY KEY(instance_id, guardian_id),
                  FOREIGN KEY(instance_id) REFERENCES encounters(instance_id)
                );
                CREATE TABLE IF NOT EXISTS claims (
                  claim_id TEXT PRIMARY KEY, instance_id TEXT NOT NULL UNIQUE,
                  owner_id TEXT NOT NULL, reward_json TEXT NOT NULL,
                  delivery_state TEXT NOT NULL DEFAULT 'pending',
                  delivery_receipt TEXT,
                  FOREIGN KEY(instance_id) REFERENCES encounters(instance_id)
                );
            """
            for statement in schema.split(";"):
                if statement.strip():
                    db.execute(statement)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(str(self.database), timeout=20, isolation_level=None)
        db.execute("PRAGMA busy_timeout=20000")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.execute("COMMIT")
        except BaseException:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
        finally:
            db.close()

    def register(self, instance_id, map_id, owner_id, room_id, guardian_ids, rewards, *, clue=None):
        for value, label in ((instance_id, "instance ID"), (map_id, "map ID"), (owner_id, "owner ID")):
            check_token(value, label)
        if type(room_id) is not int or not 10000 <= room_id < 16000:
            raise TreasureError("Treasure must be in wilderness")
        if type(guardian_ids) is not list or not 1 <= len(guardian_ids) <= 5:
            raise TreasureError("Expected 1-5 unique guardian instances")
        for guardian in guardian_ids:
            check_token(guardian, "guardian instance ID")
        if len(set(guardian_ids)) != len(guardian_ids):
            raise TreasureError("Duplicate guardian instance")
        if clue is not None:
            clue = canonical_clue(clue)
        guard = json.dumps(guardian_ids, separators=(",", ":"))
        reward = canonical_reward(rewards)
        desired = (instance_id, map_id, owner_id, room_id, guard, reward)
        with self.transaction() as db:
            existing = db.execute("SELECT * FROM encounters WHERE instance_id=?", (instance_id,)).fetchone()
            if existing is not None:
                if existing != desired:
                    raise TreasureError("Encounter ID reused with different contents")
                recorded = db.execute("SELECT clue FROM map_clues WHERE instance_id=?", (instance_id,)).fetchone()
                if (recorded is not None and recorded[0] != clue) or (recorded is None and clue is not None):
                    raise TreasureError("Encounter clue changed after activation")
                return instance_id
            try:
                db.execute("INSERT INTO encounters VALUES (?,?,?,?,?,?)", desired)
            except sqlite3.IntegrityError as exc:
                raise TreasureError("Treasure map has already been activated") from exc
            if clue is not None:
                db.execute("INSERT INTO map_clues(instance_id,clue) VALUES(?,?)", (instance_id, clue))
        return instance_id

    def locate(self, owner_id, carried_map_ids, map_id=None):
        """Return a clue only for an activated map the character carries.

        Native `locate [map ID]` must supply the carried_map_ids by walking the
        authenticated player's real inventory immediately before this call.
        It must NEVER accept player-submitted IDs as inventory proof. This
        implementation deliberately reveals no destination room or coordinates.
        """
        check_token(owner_id, "owner ID")
        held = checked_inventory_map_ids(carried_map_ids)
        if map_id is not None:
            check_token(map_id, "map ID")
            if map_id not in held:
                raise MapNotHeld("You must carry the matching treasure map to locate its clues")
        with self.transaction() as db:
            rows = db.execute(
                "SELECT e.map_id,c.clue FROM encounters e "
                "JOIN map_clues c ON c.instance_id=e.instance_id "
                "WHERE e.owner_id=?", (owner_id,)
            ).fetchall()
            matches = [(mid, clue) for mid, clue in rows if mid in held and
                       (map_id is None or mid == map_id)]
            if not matches:
                raise MapNotHeld("You must carry an activated treasure map to locate its clues")
            if len(matches) != 1:
                raise TreasureError("Multiple treasure maps: use locate <map ID>")
            mid, clue = matches[0]
            return {"map_id": mid, "clue": clue}

    def record_verified_kill(self, instance_id, guardian_id, combat_event_id, killer_id):
        """Only a trusted native-combat integration may invoke this method."""
        for value, label in ((instance_id, "instance"), (guardian_id, "guardian"),
                             (combat_event_id, "combat event"), (killer_id, "killer")):
            check_token(value, label)
        with self.transaction() as db:
            row = db.execute("SELECT guardians FROM encounters WHERE instance_id=?", (instance_id,)).fetchone()
            if row is None:
                raise TreasureError("Unknown encounter")
            guardians = json.loads(row[0])
            if guardian_id not in guardians:
                raise TreasureError("Guardian does not belong to encounter")
            prior_event = db.execute("SELECT instance_id, guardian_id, killer_id FROM defeats WHERE combat_event_id=?",
                                     (combat_event_id,)).fetchone()
            if prior_event is not None:
                if prior_event != (instance_id, guardian_id, killer_id):
                    raise TreasureError("Combat event ID reused")
            else:
                old_kill = db.execute("SELECT combat_event_id FROM defeats WHERE instance_id=? AND guardian_id=?",
                                      (instance_id, guardian_id)).fetchone()
                if old_kill:
                    raise TreasureError("Guardian already defeated; different event rejected")
                db.execute("INSERT INTO defeats VALUES (?,?,?,?)",
                           (instance_id, guardian_id, combat_event_id, killer_id))
            killed = db.execute("SELECT count(*) FROM defeats WHERE instance_id=?", (instance_id,)).fetchone()[0]
            return killed == len(guardians)

    @staticmethod
    def _claim_row(row):
        return {"claim_id": row[0], "instance_id": row[1], "owner_id": row[2],
                "rewards": json.loads(row[3]), "delivery_state": row[4],
                "delivery_receipt": row[5]}

    def claim(self, instance_id, owner_id, carried_map_ids=None):
        """No claim or claim replay is returned without current map possession.

        Native implementation must pass a fresh, trusted inventory snapshot.
        Missing snapshots fail closed, including for previously created claims.
        """
        check_token(instance_id, "instance ID")
        check_token(owner_id, "owner ID")
        held = checked_inventory_map_ids(carried_map_ids)
        with self.transaction() as db:
            encounter = db.execute("SELECT owner_id, guardians, reward_json, map_id FROM encounters WHERE instance_id=?",
                                   (instance_id,)).fetchone()
            if encounter is None:
                raise TreasureError("Unknown encounter")
            if encounter[0] != owner_id:
                raise TreasureError("Treasure map belongs to another player")
            if encounter[3] not in held:
                raise MapNotHeld("You must carry the matching treasure map to claim this chest")
            row = db.execute("SELECT * FROM claims WHERE instance_id=?", (instance_id,)).fetchone()
            if row:
                return self._claim_row(row)
            killed = db.execute("SELECT count(*) FROM defeats WHERE instance_id=?", (instance_id,)).fetchone()[0]
            if killed != len(json.loads(encounter[1])):
                raise GuardiansRemain("All treasure guardians must be defeated before claiming")
            claim_id = secrets.token_hex(16)
            db.execute("INSERT INTO claims(claim_id,instance_id,owner_id,reward_json) VALUES(?,?,?,?)",
                       (claim_id, instance_id, owner_id, encounter[2]))
            return self._claim_row(db.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone())

    def acknowledge_native_delivery(self, claim_id, owner_id, persisted_receipt):
        """Acknowledge only AFTER native inventory has saved the same claim key.

        Caller is responsible for persisted native item-idempotency checks.
        """
        for value, label in ((claim_id, "claim ID"), (owner_id, "owner ID"),
                             (persisted_receipt, "native delivery receipt")):
            check_token(value, label)
        with self.transaction() as db:
            row = db.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
            if row is None or row[2] != owner_id:
                raise TreasureError("Unknown claim or claimant")
            if row[4] == "delivered":
                if row[5] != persisted_receipt:
                    raise TreasureError("Conflicting receipt for completed claim")
                return self._claim_row(row)
            db.execute("UPDATE claims SET delivery_state='delivered',delivery_receipt=? WHERE claim_id=?",
                       (persisted_receipt, claim_id))
            return self._claim_row(db.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone())
