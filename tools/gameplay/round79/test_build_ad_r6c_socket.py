"""Strict R6C generator tests; no test-only command leaks to normal candidate."""
import unittest
from build_ad_r6c_socket_fixture import build as fixture
from build_ad_r6c_socket_replay import build as replay

FIXTURE='''#include "hd79_ad_four_store.h"
void fake(void) {
    if(!strcmp(action,"pending")) {
        return 0;
    }
}
'''
REPLAY='''SOURCE.parent.name.startswith("hd-army-game-round79addeath-")
        for mount_id in range(1,7):
            if mount_id==1:
                ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")
'''

class GeneratorTests(unittest.TestCase):
    def test_fixture_has_private_test_gate(self):
        s=fixture(FIXTURE)
        self.assertIn('HD79_AD_CREATURE_ACTION_PLAYTEST',s)
        self.assertIn('hd79_ad_creature_action(owner',s)
        self.assertIn('r6ctune',s)
        self.assertNotIn('R6C ACTION COMPLETE',FIXTURE)
    def test_no_duplicates(self):
        with self.assertRaises(ValueError):fixture(FIXTURE+FIXTURE)
        with self.assertRaises(ValueError):fixture('no anchors')
        with self.assertRaises(ValueError):fixture(fixture(FIXTURE))
    def test_socket_preserves_genuine_six_deaths(self):
        s=replay(REPLAY)
        self.assertIn('hd-army-game-round79adcreature-',s)
        self.assertIn('R6C ACTION COMPLETE',s)
        self.assertIn('R6C NATIVE TARGET PREPARED',s)
        self.assertIn('R6C: PRIVATE NATIVE PHYSICAL BOARD/DISMOUNT SOCKET PASS',s)
        self.assertIn('ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")',s)
    def test_replay_rejects_drift(self):
        with self.assertRaises(ValueError):replay('bad')
        with self.assertRaises(ValueError):replay(REPLAY+REPLAY)
        with self.assertRaises(ValueError):replay(replay(REPLAY))

if __name__=='__main__':unittest.main()
