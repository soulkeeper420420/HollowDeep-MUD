"""Round79AB: strict private source/ID/2-fragment lockout staging tests."""
from pathlib import Path
import tempfile
import unittest
import hashlib
import stage_mount_presence_store_round79ab as stage

STORE='''#ifdef HD79_MOUNT_STORE_PLAYTEST
#include "hd79_mount_ids.h"
#endif
static int reserved_receipt(const char *claim) {
 return !strcmp(claim, hd79_mount_b_id);
}
#ifdef HD79_MOUNT_STORE_PLAYTEST
#include "hd79_mount_store.inc"
#endif
'''
OLD='''static int hd79_mount_transaction(const char *name, void *e,void *d,void *o)
{
    return 0;
}
int hd79_mount_store_init(const char *name, void *out)
{
    return hd79_mount_transaction(name,NULL,NULL,out);
}
int hd79_mount_store_commit(const char *name, void *expected,
                             void *next, void *out)
{
    return hd79_mount_transaction(name,expected,next,out);
}
'''
MAKE='''ifeq ($(MOUNT_STABLECHECK_PLAYTEST),1)
CFLAGS += -DHD79_MOUNT_STABLECHECK_PLAYTEST
endif
'''

class NativePresenceStage(unittest.TestCase):
    def setUp(self):
        self.a=tempfile.TemporaryDirectory(prefix='hd-army-game-round79stable-test-',dir='/tmp')
        self.b=tempfile.TemporaryDirectory(prefix='hd-army-game-round79presence-test-',dir='/tmp')
        self.addCleanup(self.a.cleanup);self.addCleanup(self.b.cleanup)
        self.src=Path(self.a.name)/'src';self.dst=Path(self.b.name)/'src'
        self.src.mkdir()
        self.data={n:'/* original */\n' for n in stage.REQUIRED}
        self.data.update({'frp.new':b'\x7fELF\x01fake',
                          'hd_player_store.c':STORE,
                          'hd79_mount_store.inc':OLD,
                          'Makefile':MAKE})
        self.data['command2.c']='/* original movement */\n'
        self.data['command6.c']='/* original movement */\n'
        self.data['wilderness.c']='/* original movement */\n'
        self.data['hd79_stablecheck.c']='/* original stable */\n'
        for n,blob in self.data.items():
            (self.src/n).write_bytes(blob if isinstance(blob,bytes) else
                                     blob.encode('latin-1'))
    def digest(self):
        return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.src.iterdir()}
    def test_only_save_and_makefile_changed(self):
        original=self.digest()
        stage.stage(self.src,self.dst)
        self.assertEqual(original,self.digest())
        before={n:(self.src/n).read_bytes() for n in self.data}
        after={n:(self.dst/n).read_bytes() for n in self.data}
        changed={n for n in before if before[n]!=after[n]}
        self.assertEqual(changed,{'hd_player_store.c',
                                  'hd79_mount_store.inc','Makefile'})
        self.assertEqual({p.name for p in self.dst.iterdir()}-set(self.data),
                         set(stage.ADD))
    def test_stored_id_reserved_once(self):
        stage.stage(self.src,self.dst)
        p=(self.dst/'hd_player_store.c').read_text()
        self.assertEqual(p.count('!strcmp(claim, HD79_MOUNT_PRESENCE_ID)'),1)
        self.assertIn('#include "hd79_mount_presence_store.inc"',p)
        self.assertIn('#include "hd79_mount_presence_store.h"',p)
    def test_old_writer_has_both_mutations_disabled(self):
        stage.stage(self.src,self.dst)
        p=(self.dst/'hd79_mount_store.inc').read_text()
        self.assertEqual(p.count('(void)name;'),2)
        self.assertEqual(p.count('return HD79_MOUNT_STORE_FAILURE;'),2)
        self.assertIn('#ifndef HD79_MOUNT_PRESENCE_STORE_PLAYTEST',p)
    def test_no_gameplay_changes(self):
        stage.stage(self.src,self.dst)
        for n in ('global.c','command1.c','command2.c','command6.c',
                  'wilderness.c','hd79_mount_command.c','hd79_stablecheck.c'):
            self.assertEqual((self.src/n).read_bytes(),(self.dst/n).read_bytes())
    def test_accepts_only_disposable_source(self):
        with self.assertRaisesRegex(ValueError,'Only disposable'):
            stage.stage(Path('/srv/hollowdeep/world/src_3.00'),self.dst)
    def test_preexisting_output_denied(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,'fresh'):
            stage.stage(self.src,self.dst)
    def test_missing_binary_denied(self):
        (self.src/'frp.new').unlink()
        with self.assertRaisesRegex(ValueError,'Missing/symlink'):
            stage.stage(self.src,self.dst)
    def test_unsafe_binary_denied(self):
        (self.src/'frp.new').write_text('not ELF32')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            stage.stage(self.src,self.dst)
    def test_id_collision_denied(self):
        p=self.src/'hd_player_store.c'
        p.write_text(p.read_text()+'/* '+stage.ID+' */\n')
        with self.assertRaisesRegex(ValueError,'collision'):
            stage.stage(self.src,self.dst)
    def test_anchor_drift_denied(self):
        p=self.src/'hd79_mount_store.inc'
        p.write_text(p.read_text().replace('static int hd79_mount_transaction',
                                           'static int unsafe_transaction'))
        with self.assertRaisesRegex(ValueError,'drift'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())
    def test_symlink_denied(self):
        (self.src/'link').symlink_to(self.src/'Makefile')
        with self.assertRaisesRegex(ValueError,'Symlinks'):
            stage.stage(self.src,self.dst)
    def test_no_repeat_stage(self):
        stage.stage(self.src,self.dst)
        another=Path(self.b.name)/'second'
        with self.assertRaisesRegex(ValueError,'Only disposable'):
            stage.stage(self.dst,another)
    def test_make_gate_depends_on_mount(self):
        stage.stage(self.src,self.dst)
        m=(self.dst/'Makefile').read_text()
        self.assertIn('MOUNT_PRESENCE_STORE_PLAYTEST requires MOUNT_STORE_PLAYTEST',m)
        self.assertIn('OBJECTS += hd79_mount_presence.o',m)

if __name__=='__main__':unittest.main()
