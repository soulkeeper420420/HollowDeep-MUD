# Round79AC3B native lifecycle fail-closed staging and hook-coverage tests.
from pathlib import Path
import hashlib
import tempfile
import unittest
import stage_mount_lifecycle_round79ac3b as stage

MAKE=('OBJECTS = main.o\n'
      'ifeq ($(MOUNT_WORLD_IDENTITY_PLAYTEST),1)\n'
      'CFLAGS += -DHD79_MOUNT_WORLD_IDENTITY_PLAYTEST\n'
      'OBJECTS += hd79_mount_world_identity.o\n'
      'endif\n'
      'frp.new: $(OBJECTS)\n'
      '\t$(CC) $(OBJECTS) -o frp.new\n')
ROOM='''
void add_crt_rom(creature *crt_ptr, room *rom_ptr, int num )
{
    ctag *t;
    crt_ptr->parent_rom = rom_ptr;
}
void del_crt_rom(creature *crt_ptr, room *rom_ptr )
{
    ctag *t;
    crt_ptr->parent_rom=0;
}
void add_ply_rom(creature *ply_ptr, room *rom_ptr )
{
    ctag *t;
    ply_ptr->parent_rom=rom_ptr;
}
void del_ply_rom(creature *ply_ptr, room *rom_ptr )
{
    ctag *t;
    ply_ptr->parent_rom=0;
}
'''
FILES='''
void free_crt( creature *crt_ptr )
{
    int i;
    free(crt_ptr);
}
void free_rom( room *rom_ptr )
{
    ctag *p;
    free(rom_ptr);
}
'''
HEAD='''#ifndef HD79_MOUNT_WORLD_IDENTITY_H
#define HD79_MOUNT_WORLD_IDENTITY_H
void hd79_world_mount_unbind_owner(const struct creature *owner);
#endif
'''
IDENT='''void hd79_world_mount_unbind_owner(const creature *owner)
{
    int x=0;
}
'''

class LifecycleStage(unittest.TestCase):
    def setUp(self):
        self.a=tempfile.TemporaryDirectory(prefix=stage.SOURCE_PREFIX+'test-',dir='/tmp')
        self.b=tempfile.TemporaryDirectory(prefix=stage.TARGET_PREFIX+'test-',dir='/tmp')
        self.addCleanup(self.a.cleanup)
        self.addCleanup(self.b.cleanup)
        self.src=Path(self.a.name)/'src'
        self.dst=Path(self.b.name)/'src'
        self.src.mkdir()
        for n in stage.NEEDED:
            (self.src/n).write_bytes(b'/* original native */\n')
        (self.src/'frp.new').write_bytes(b'\x7fELF\x01mock')
        for n,v in {'Makefile':MAKE,'room.c':ROOM,'files1.c':FILES,
                    'hd79_mount_world_identity.h':HEAD,
                    'hd79_mount_world_identity.c':IDENT}.items():
            (self.src/n).write_text(v)

    def test_exact_private_patch_and_preserve_baseline(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.src.iterdir()}
        stage.stage(self.src,self.dst)
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in self.src.iterdir()})
        changed={p.name for p in self.src.iterdir()
                 if p.read_bytes()!=(self.dst/p.name).read_bytes()}
        self.assertEqual(changed,set(stage.FILES))
        out=(self.dst/'room.c').read_text()
        self.assertEqual(out.count('hd79_world_mount_unbind_creature(crt_ptr);'),2)
        self.assertEqual(out.count('hd79_world_mount_unbind_owner(ply_ptr);'),2)
        free=(self.dst/'files1.c').read_text()
        self.assertIn('hd79_world_mount_unbind_all();',free)
        self.assertEqual(free.count('hd79_world_mount_unbind_creature(crt_ptr);'),1)
        self.assertEqual(free.count('hd79_world_mount_unbind_owner(crt_ptr);'),1)
        mk=(self.dst/'Makefile').read_text()
        self.assertLess(mk.index('MOUNT_LIFECYCLE_PLAYTEST'),mk.index('frp.new:'))
        self.assertIn('requires MOUNT_WORLD_IDENTITY_PLAYTEST=1',mk)

    def test_all_clear_function_decl_and_body(self):
        stage.stage(self.src,self.dst)
        h=(self.dst/'hd79_mount_world_identity.h').read_text()
        c=(self.dst/'hd79_mount_world_identity.c').read_text()
        self.assertIn('void hd79_world_mount_unbind_all(void);',h)
        self.assertIn('void hd79_world_mount_unbind_all(void)',c)
        self.assertIn('memset(registry,0,sizeof registry);',c)

    def test_cannot_modify_production(self):
        with self.assertRaisesRegex(ValueError,'Disposable /tmp'):
            stage.stage(Path('/srv/hollowdeep/world/src_3.00'),self.dst)

    def test_bad_elf(self):
        (self.src/'frp.new').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            stage.stage(self.src,self.dst)

    def test_existing_destination(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,'fresh'):
            stage.stage(self.src,self.dst)

    def test_symlinks(self):
        (self.src/'ref').symlink_to(self.src/'room.c')
        with self.assertRaisesRegex(ValueError,'Symlink'):
            stage.stage(self.src,self.dst)

    def test_native_signature_drift(self):
        p=self.src/'files1.c'
        p.write_text(p.read_text().replace('void free_crt(', 'void delete_crt('))
        with self.assertRaisesRegex(ValueError,'free_crt'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_identity_source_drift(self):
        p=self.src/'hd79_mount_world_identity.c'
        p.write_text(p.read_text().replace('hd79_world_mount_unbind_owner','old_fn'))
        with self.assertRaisesRegex(ValueError,'identity'):
            stage.stage(self.src,self.dst)

    def test_make_anchor_drift(self):
        p=self.src/'Makefile'
        p.write_text(p.read_text().replace('hd79_mount_world_identity.o','bad.o'))
        with self.assertRaisesRegex(ValueError,'AC2 feature gate'):
            stage.stage(self.src,self.dst)

    def test_no_unintended_gameplay_save_edit(self):
        stage.stage(self.src,self.dst)
        for name in ('hd_player_store.c','hd79_mount_command.c','global.c',
                     'wilderness.c','command1.c','command2.c','command5.c',
                     'command6.c','hd79_mount_presence_store.inc'):
            self.assertEqual((self.src/name).read_bytes(),
                             (self.dst/name).read_bytes())

    def test_identity_hooks_never_create_mount(self):
        stage.stage(self.src,self.dst)
        for name in ('room.c','files1.c'):
            s=(self.dst/name).read_text()
            self.assertNotIn('hd79_world_mount_bind(',s)
            self.assertNotIn('hd79_mount_award(',s)

    def test_repeat_stage_rejected(self):
        stage.stage(self.src,self.dst)
        with self.assertRaises(ValueError):
            stage.stage(self.src,self.dst)

if __name__=='__main__':
    unittest.main()
