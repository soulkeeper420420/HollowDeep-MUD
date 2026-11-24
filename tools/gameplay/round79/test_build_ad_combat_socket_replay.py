"""Guard the extension of the pinned private native gameplay replay."""
import unittest
import build_ad_combat_socket_replay as replay


class CombatReplay(unittest.TestCase):
    def source(self):
        return ('SOURCE.parent.name.startswith("hd-army-game-round79stable-")\n'
                '        prior["quit_with_cooldown"](returning,process)\n'
                'finally:\n    if process is not None: pass\n')

    def test_death_fault_restart_and_duplicate_assertions_are_required(self):
        result=replay.build(self.source())
        for marker in ('SIX REAL NATIVE COMBAT DEATHS PASS',
                       'You killed', 'failbefore', 'failafter', 'pending=1',
                       'mask=63 serial=13 count=6', 'process.terminate()',
                       'AD FIXTURE DENIED', 'Mount death save pending'):
            self.assertIn(marker,result)

    def test_source_drift_fails_closed(self):
        with self.assertRaises(ValueError): replay.build('unrelated replay')

    def test_ambiguous_replay_fails_closed(self):
        with self.assertRaises(ValueError): replay.build(self.source()*2)


if __name__=='__main__': unittest.main()
