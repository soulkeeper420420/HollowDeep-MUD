"""Strict generators accept R5 fixtures only; all test changes remain private."""
import unittest
from pathlib import Path
from build_ad_r6b_socket_fixture import build as fixture_build
from build_ad_r6b_socket_replay import build as replay_build

class R6BSocketBuilders(unittest.TestCase):
    def test_fixture_rejects_missing_header(self):
        with self.assertRaises(ValueError):fixture_build('bad')

    def test_fixture_requires_private_cas_flag(self):
        input='#include "hd79_ad_four_store.h"\n    if(!strcmp(action,"pending")) {'
        patched=fixture_build(input)
        self.assertIn('#ifndef HD79_AD_ACTION_CAS_PLAYTEST',patched)
        self.assertIn('hd79_ad_four_action_commit_native',patched)

    def test_fixture_duplicate_anchor_denied(self):
        input='#include "hd79_ad_four_store.h"\n'*2
        with self.assertRaises(ValueError):fixture_build(input)

    def test_replay_rejects_wrong_source(self):
        with self.assertRaises(ValueError):replay_build('bad')

    def test_replay_rejects_missing_native_action(self):
        with self.assertRaises(ValueError):replay_build(
            'SOURCE.parent.name.startswith("hd-army-game-round79addeath-")')

    def test_replay_cas_and_all_six_deaths(self):
        text='''SOURCE.parent.name.startswith("hd-army-game-round79addeath-")
            if mount_id==1:
                ask(returning,"adfixture failbefore","AD FIXTURE FAULT ARMED")
'''
        final=replay_build(text)
        self.assertIn('R6B ACTION UNCERTAIN',final)
        self.assertIn('native R6B action CAS board/dismount',final)
        self.assertIn('hd-army-game-round79adcas-',final)

if __name__=='__main__':unittest.main()
