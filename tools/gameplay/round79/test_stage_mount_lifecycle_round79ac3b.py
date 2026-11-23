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

    def test_native_same_line_open_braces(self):
        # Native source may place a function body brace on the same line.
        for filename,names in (('room.c',
              ('add_crt_rom','del_crt_rom','add_ply_rom','del_ply_rom')),
              ('files1.c',('free_crt','free_rom'))):
            p=self.src/filename
            body=p.read_text()
            for fn in names:
                # Change ONLY the one definition, not unrelated braces.
                pattern=r'(void\s+'+fn+r'\s*\([^)]*\))\s*\n\s*\{'
                import re
                result,count=re.subn(pattern,r'\1 {',body,count=1)
                self.assertEqual(count,1,fn)
                body=result
            p.write_text(body)
        stage.stage(self.src,self.dst)
        out=(self.dst/'room.c').read_text()
        self.assertEqual(out.count('hd79_world_mount_unbind_creature(crt_ptr);'),2)
        self.assertEqual(out.count('hd79_world_mount_unbind_owner(ply_ptr);'),2)
        self.assertEqual((self.dst/'files1.c').read_text().count(
                         'hd79_world_mount_unbind_all();'),1)

    def test_multiline_native_function_parameters(self):
        p=self.src/'room.c'
        original=p.read_text()
        name='void add_crt_rom(creature *crt_ptr, room *rom_ptr, int num )'
        multiline=('void\nadd_crt_rom(\n'
                   ' creature *crt_ptr,\n room *rom_ptr,\n int num\n)')
        self.assertEqual(original.count(name),1)
        p.write_text(original.replace(name,multiline))
        stage.stage(self.src,self.dst)
        self.assertIn('hd79_world_mount_unbind_creature(crt_ptr);',
                      (self.dst/'room.c').read_text())

    def test_prototype_alone_cannot_be_hooked(self):
        p=self.src/'room.c'
        src=p.read_text()
        import re
        src,n=re.subn(
            r'void\s+add_crt_rom\s*\([^)]*\)\s*\{[^}]*\}',
            'void add_crt_rom(creature *crt_ptr, room *rom_ptr, int num);',
            src,count=1)
        self.assertEqual(n,1)
        p.write_text(src)
        with self.assertRaisesRegex(ValueError,'add_crt_rom'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_exact_kr_style_all_six_native_definitions(self):
        # Reproduce native Round79AC3B R2 Linode signature:
        # 'void add_crt_rom(crt_ptr, rom_ptr, num)'
        # with typed K&R declarations before the opening brace.
        import re
        for file,names in (('room.c',(
                'add_crt_rom','del_crt_rom','add_ply_rom','del_ply_rom')),
                           ('files1.c',('free_crt','free_rom'))):
            p=self.src/file
            content=p.read_text()
            for name in names:
                expected=stage.KNR_PARAMETERS[name]
                decls=', '.join(param for typ,param,pointer in expected)
                declarations='\n'.join(
                    typ+' '+('*' if pointer else '')+param+';'
                    for typ,param,pointer in expected)
                pattern=r'(?m)^void\s+'+name+r'\s*\([^)]*\)\s*\{'
                replacement='void '+name+'('+decls+')\n'+declarations+'\n{'
                content,num=re.subn(pattern,lambda m: replacement,content,count=1)
                self.assertEqual(num,1,name)
            p.write_text(content)
        stage.stage(self.src,self.dst)
        room=(self.dst/'room.c').read_text()
        self.assertIn('void add_crt_rom(crt_ptr, rom_ptr, num)',room)
        self.assertEqual(room.count('hd79_world_mount_unbind_creature(crt_ptr);'),2)
        self.assertEqual(room.count('hd79_world_mount_unbind_owner(ply_ptr);'),2)
        files=(self.dst/'files1.c').read_text()
        self.assertIn('hd79_world_mount_unbind_all();',files)
        self.assertEqual(files.count('hd79_world_mount_unbind_owner(crt_ptr);'),1)

    def test_kr_wrong_typed_parameter_rejected(self):
        p=self.src/'room.c'
        content=p.read_text()
        old='void add_crt_rom(creature *crt_ptr, room *rom_ptr, int num )\n{'
        new=('void add_crt_rom(crt_ptr, rom_ptr, num)\n'
             'creature *crt_ptr;\ncreature *rom_ptr;\nint num;\n{')
        self.assertEqual(content.count(old),1)
        p.write_text(content.replace(old,new))
        with self.assertRaisesRegex(ValueError,'add_crt_rom'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_kr_missing_declaration_rejected(self):
        p=self.src/'files1.c'
        content=p.read_text()
        old='void free_rom( room *rom_ptr )\n{'
        new='void free_rom(rom_ptr)\n{'
        self.assertEqual(content.count(old),1)
        p.write_text(content.replace(old,new))
        with self.assertRaisesRegex(ValueError,'free_rom'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_kr_duplicate_definition_rejected(self):
        p=self.src/'room.c'
        content=p.read_text()
        self.assertEqual(content.count('void del_crt_rom('),1)
        p.write_text(content+'\n'+content[content.index('void del_crt_rom('):])
        with self.assertRaisesRegex(ValueError,'del_crt_rom'):
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
