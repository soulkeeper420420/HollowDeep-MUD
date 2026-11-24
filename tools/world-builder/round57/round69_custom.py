"""Round 69: custom native serialization, rejection, and isolated gameplay."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import string
import struct
import sys
import time
from unittest.mock import patch
import zipfile

import app

ROOM=8900

def plan():
    candidate=app.new_plan(14,15)
    candidate['rooms'].append(dict(room_id=ROOM,new_room=True,name='Round 69 Portal',
                                   exits=[],monsters=[],objects=[]))
    a=candidate['rooms'][0]
    b=candidate['rooms'][-1]
    a['name']='Round 69 Gateway'
    a['exits'].append(dict(direction='archway',destination=ROOM,return_direction='threshold'))
    b['exits'].append(dict(direction='threshold',destination=14,return_direction='archway'))
    base_monster=1
    base_object=1
    assert base_monster in app.TEMPLATES and base_object in app.OBJECT_TEMPLATES
    m_id=next(i for i in range(999,0,-1) if i not in app.TEMPLATES)
    o_id=next(i for i in range(999,0,-1) if i not in app.OBJECT_TEMPLATES)
    candidate['custom_templates']={
        'monsters':[dict(id=m_id,base_id=base_monster,name='Round 69 Practice Golem')],
        'objects':[dict(id=o_id,base_id=base_object,name='Round 69 Practice Blade')],
    }
    b['monsters']=[dict(id=m_id,count=1,respawn=60)]
    b['objects']=[dict(id=o_id,count=1,respawn=60)]
    return candidate

def reject(candidate,phrase):
    try:
        app.area.clean_plan(candidate)
    except (ValueError,TypeError) as ex:
        assert phrase.lower() in str(ex).lower(), (phrase,ex)
    else:
        raise AssertionError('Accepted invalid custom plan: '+phrase)

def tests():
    p=plan()
    cleaned=app.area.clean_plan(p)
    assert ROOM in cleaned
    ids,assets=app.custom_banks(p)
    assert ids['monsters']=={p['custom_templates']['monsters'][0]['id']}
    assert ids['objects']=={p['custom_templates']['objects'][0]['id']}
    for kind,short,size,records,base,offset,width in [
        ('monsters','m',app.ABI['creature'],app.ABI['per_file'],1,app.ABI['name'],app.ABI['name_size']),
        ('objects','o',app.object_size,app.per_file,1,0,app.name_size)]:
        id_group,id_slot=divmod(p['custom_templates'][kind][0]['id'],records)
        base_group,base_slot=divmod(base,records)
        name=f'objmon/{short}{id_group:02d}'
        assert name in assets
        actual=assets[name][id_slot*size:(id_slot+1)*size]
        origin=(app.ROOT/'templates'/f'{short}{base_group:02d}').read_bytes()[base_slot*size:(base_slot+1)*size]
        display_name=p['custom_templates'][kind][0]['name']
        identifier=p['custom_templates'][kind][0]['id']
        expected=bytearray(origin)
        expected[offset:offset+width]=app.area.r51.encode_name(display_name,width)
        key_start=255 if kind=='monsters' else 160
        free=next((key_start+20*k for k in range(3)
                   if origin[key_start+20*k]==0),None)
        assert free is not None,kind
        alias=(('hdm' if kind=='monsters' else 'hdo')
               +str(identifier)).encode()
        expected[free:free+20]=alias.ljust(20,bytes(1))
        assert actual==bytes(expected),f'Unexpected native {kind} bytes'
        assert hashlib.sha256(assets[name]).hexdigest()
    print('ROUND 69: custom creature and object native ABI records PASS',flush=True)
    with __import__('tempfile').TemporaryDirectory(prefix='round69-zip-') as tmp:
        with patch.object(app.area,'EXPORTS',Path(tmp)):
            result=app.area.generate(p)
        bundle=(Path(tmp)/(result['export_id']+'.zip')).read_bytes()
        assert hashlib.sha256(bundle).hexdigest()==result['bundle_sha256']
        with zipfile.ZipFile(io.BytesIO(bundle)) as z:
            assert z.testzip() is None
            entries=set(z.namelist())
            assert 'r08900.native-candidate' in entries and 'manifest.json' in entries
            assert any(x.startswith('objmon/m') for x in entries)
            assert any(x.startswith('objmon/o') for x in entries)
            native=z.read('r08900.native-candidate')
            parsed=app.area.parse(native)
            assert parsed['id']==ROOM
            exits,_=app.area.r51.original_exits(native)
            assert app.area.r51.fields(exits[0])=={'direction':'threshold','destination':14}
            assert all(result['rooms'][str(ROOM)]['checks'].values())
            assert all(z.read(name) for name in entries if name.startswith('objmon/'))
    print('ROUND 69: newly authored room ZIP and manifest PASS',flush=True)
    invalid=copy.deepcopy(p)
    invalid['rooms'].append(copy.deepcopy(invalid['rooms'][-1]))
    reject(invalid,'duplicate')
    invalid=copy.deepcopy(p)
    invalid['rooms'][-1]['room_id']=8800
    reject(invalid,'8900')
    invalid=copy.deepcopy(p)
    invalid['rooms'][-1]['exits'].clear()
    reject(invalid,'reciprocal')
    invalid=copy.deepcopy(p)
    invalid['rooms'][0]['exits'][-1]['direction']='Upper Hall'
    reject(invalid,'lowercase')
    invalid=copy.deepcopy(p)
    invalid['custom_templates']['monsters'][0]['base_id']=123456
    reject(invalid,'base template')
    invalid=copy.deepcopy(p)
    invalid['custom_templates']['objects'][0]['id']=1
    reject(invalid,'collides')
    invalid=copy.deepcopy(p)
    invalid['rooms'][-1]['monsters'][0]['id']=-1
    reject(invalid,'unknown')
    invalid=copy.deepcopy(p)
    invalid['rooms'][0]['exits'].append(dict(direction='arch',destination=ROOM,return_direction='portal'))
    invalid['rooms'][-1]['exits'].append(dict(direction='portal',destination=14,return_direction='arch'))
    reject(invalid,'overlap')
    print('ROUND 69: invalid IDs, labels, templates and exits rejected PASS',flush=True)

def install_custom(stage,check):
    manifest=json.loads((stage/'round69-browser.json').read_text())
    p=manifest['plan']; result=manifest['result']
    assert p==plan(), 'Browser authored plan differs from canonical native test plan'
    bundle=(stage/'round69-browser.zip').read_bytes()
    check(hashlib.sha256(bundle).hexdigest()==result['bundle_sha256'],
          'Round 69 browser custom ZIP checksum')
    target=stage/'custom/rootfs'
    with zipfile.ZipFile(io.BytesIO(bundle)) as z:
        assert z.testzip() is None
        listed=set(z.namelist()); advertised=set(result['rooms'])
        assert advertised=={str(x['room_id']) for x in p['rooms']}
        banks={name for name in listed if name.startswith('objmon/')}
        assert len(banks)==2 and any(n.startswith('objmon/m') for n in banks) and any(n.startswith('objmon/o') for n in banks)
        expected={'manifest.json',*(f"r{x['room_id']:05d}.native-candidate" for x in p['rooms']),*banks}
        assert listed==expected,(listed,expected)
        zip_manifest=json.loads(z.read('manifest.json'))
        for name in banks:
            assert hashlib.sha256(z.read(name)).hexdigest()==zip_manifest['template_banks'][name]
        for x in p['rooms']:
            rid=x['room_id']; name=f'r{rid:05d}.native-candidate'
            data=z.read(name)
            assert hashlib.sha256(data).hexdigest()==zip_manifest['rooms'][str(rid)]['candidate_sha256']
            assert all(zip_manifest['rooms'][str(rid)]['checks'].values())
            if rid!=ROOM:
                native,_=app.area.r50.baseline(rid)
                old,_=app.area.r51.original_exits(native)
                new,_=app.area.r51.original_exits(data)
                assert all(record in new for record in old)
            dst=target/'rooms'/f'r{rid:05d}'
            dst.write_bytes(data)
            shutil.copystat(target/'rooms/r00001',dst)
            os.chown(dst,65534,65534)
        for name in banks:
            dst=target/name
            dst.write_bytes(z.read(name))
            shutil.copystat(target/'objmon/m00',dst)
            os.chown(dst,65534,65534)
    check(True,'Round 69 native ZIP preserves existing room records and adds isolated template banks')
    return target

def native_gameplay(stage,scope,check):
    target=install_custom(stage,check)
    scope.update(root=target,PORT=4045,process=None,clients=[])
    scope['start_server']()
    try:
        token=lambda n:''.join(secrets.choice(string.ascii_lowercase) for _ in range(n))
        player=scope['new_character']('Hd'+token(7),'Test'+token(9))
        def command(text):
            output=scope['command'](player,text)
            print('ROUND69 > '+text+'\n'+output[:900],flush=True)
            return output.lower()
        check('round 69 gateway' in command('north'),'Round 69 original start route reaches room 14')
        arrival=command('archway')
        if 'round 69 portal' not in arrival:
            arrival=command('go archway')
        check('round 69 portal' in arrival,'Round 69 custom named exit reaches new native room')
        look=command('look')
        check('you see a round 69 practice golem.' in look,'Round 69 custom monster visibly spawned')
        check('round 69 practice blade' in look,'Round 69 custom object visibly spawned')
        obj=json.loads((stage/'round69-browser.json').read_text())['plan']['custom_templates']['objects'][0]
        pickup=command('get hdo'+str(obj['id']))
        check('round 69 practice blade' in pickup or 'round 69 practice blade' in command('inventory'),
              'Round 69 custom object picked up')
        check('round 69 practice blade' in command('inventory'), 'Round 69 custom object in native inventory')
        rng=target/'hollowdeep-data/round11q-rng'
        rng.write_text('199');rng.chmod(0o644)
        try:
            defeated=False
            target=None
            # The custom record has a new display name. The old base alias
            # "boss" is not necessarily an alias for the renamed monster.
            monster=json.loads((stage/'round69-browser.json').read_text())['plan']['custom_templates']['monsters'][0]
            for candidate in ('hdm'+str(monster['id']),):
                hit=command('attack '+candidate)
                if 'you killed' in hit and 'golem' in hit:
                    target=candidate
                    defeated=True
                    break
                if ("you don't see that here" not in hit and
                    'does not exist' not in hit and 'do not see' not in hit):
                    target=candidate
                    break
            check(target is not None, 'Round 69 lowercase custom command keyword targets the native monster')
            if not defeated:
                for _ in range(20):
                    hit=command('attack '+target)
                    if 'you killed' in hit and 'golem' in hit:
                        defeated=True
                        break
                    if "you don't see that here" in hit:
                        raise AssertionError('Renamed monster target became unresolvable in combat')
                    time.sleep(3)
        finally:
            rng.unlink(missing_ok=True)
        check(defeated,'Round 69 custom monster defeated in native combat')
        look=command('look')
        check('round 69 portal' in look and
              'you see a round 69 practice golem.' not in look,
              'Round 69 defeated custom monster absent')
        return_trip=command('threshold')
        if 'round 69 gateway' not in return_trip:return_trip=command('go threshold')
        check('round 69 gateway' in return_trip,'Round 69 named return exit reaches original room')
        time.sleep(65)
        revisit=command('archway')
        if 'round 69 portal' not in revisit:revisit=command('go archway')
        check('round 69 portal' in revisit,'Round 69 custom exit remains usable')
        check('you see a round 69 practice golem.' in revisit or
              'you see a round 69 practice golem.' in command('look'),
              'Round 69 custom monster respawns in native gameplay')
    finally:
        for client in scope['clients']:client.close()
        scope['stop_server']()

if __name__=='__main__':
    if '--test' in sys.argv:tests()
