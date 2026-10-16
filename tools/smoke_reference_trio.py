"""Cold-boot all selections and exercise all five reference revisions in matches."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from headless_snes import Emulator
from build_reference_trio import SPECS, BASE_SHA

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--rom',type=Path,required=True);p.add_argument('--base-rom',type=Path,required=True)
p.add_argument('--base-manifest',type=Path,required=True);p.add_argument('--art-dir',type=Path,required=True)
p.add_argument('--pair-art-dir',type=Path,required=True);p.add_argument('--core',type=Path,required=True)
p.add_argument('--output-dir',type=Path,required=True)
a=p.parse_args();out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
base=a.base_rom.read_bytes();rom=a.rom.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
rows=json.loads(a.base_manifest.read_text())['rows']
modified={2,3,4}
for i,row in enumerate(rows):
 off=row['profile_offset'];changed=[j for j in range(298)if base[off+j]!=rom[off+j]]
 assert not changed or i in modified
 assert all(j in [2,4,5] or 286<=j<298 for j in changed)
# Accepted pair head streams, raw modular arm/hips and palette category slots.
for start,length in [(0xe7e0f,0x1800),(0xc0e14,0x1800),(0x2fc800,0x4000),(0x320800,0x4000),
 (0x330800,0x4000),(0x340800,0x4000),(0x1e500,50)]:assert rom[start:start+length]==base[start:start+length]
for rank in [0,1]:
 face=rows[rank]['face_id'];assert rom[0x5d07e+face*32:0x5d07e+face*32+32]==base[0x5d07e+face*32:0x5d07e+face*32+32]
assert sum(rom)&65535==struct.unpack_from('<H',rom,0xffde)[0]
e=Emulator(a.rom,a.core);e.core.retro_set_controller_port_device(1,1)
assert not any(C.string_at(e.core.retro_get_memory_data(0),32768))
def ram():return C.string_at(e.core.retro_get_memory_data(2),131072)
def word(addr):return struct.unpack_from('<H',ram(),addr)[0]
def tap(key,port=0):
 if port==0:e.press(key,4);e.run(150 if key=='b' else 45)
 else:e.extra_buttons[port]={e.keys[key]};e.run(4);e.extra_buttons[port]=set();e.run(162 if key=='b' else 57)
def dual(n,keys,port):
 if port==0:e.run(n,keys)
 else:e.extra_buttons[port]={e.keys[k]for k in keys};e.run(n);e.extra_buttons[port]=set()
def cursor(target,port=0):
 current=word(0x1887);assert current<16
 for _ in range(abs(target//4-current//4)):tap('down' if target//4>current//4 else 'up',port)
 for _ in range(abs(target%4-current%4)):tap('right' if target%4>current%4 else 'left',port)
 assert word(0x1887)==target,(target,word(0x1887))
e.run(1200);tap('start');e.run(150);tap('down');tap('b');e.run(150);e.save(out/'options.state')
tap('right');tap('start');e.run(450)
for pg in range(6):
 assert word(0x1885)==(16 if pg<5 else 4)
 e.save(out/f'page-{pg}.state');tap('r')
assert word(0x1881)==0
expected_models={0:8,1:9,2:26,3:56,4:28};selected=[]
for i,row in enumerate(rows):
 e.load(out/f'page-{i//16}.state');e.run(1)
 for _ in range(i%16//4):tap('down')
 for _ in range(i%4):tap('right')
 model=expected_models.get(i,row['body_id']);assert word(0x17fd)==model,(i,model,word(0x17fd))
 if i<5:e.image(out/(['austin','rock','hhh','undertaker','mankind'][i]+'-selection.png'))
 selected.append({'rank':i+1,'model':model})
print('PASS 84 selections and page counts',flush=True)
heads={label:(a.art_dir/(label+'-heads.bin')).read_bytes()for label in SPECS}
heads.update({label:(a.pair_art_dir/(label+'-heads.bin')).read_bytes()for label in ['austin','rock']})
parts={label:s['parts']for label,s in SPECS.items()};parts.update({'austin':{0xcc:0xefc8},'rock':{0xc8:0xf308,0xca:0xf208,0xcc:0xf408}})
matches=[]
for first,second,labels in [(2,3,('hhh','undertaker')),(4,0,('mankind','austin')),(1,2,('rock','hhh'))]:
 e.load(out/'page-0.state');e.run(1);cursor(first);tap('b');tap('b');cursor(second,1);tap('b',1);tap('b',1)
 tap('start');e.run(450);e.image(out/('-'.join(labels)+'-versus.png'));tap('b');e.run(900);e.run(240)
 for port,label in enumerate(labels):
  address=0x8000+port*0x2000;assert ram()[address:address+0x1800]==heads[label],(labels,port,'head load')
  for field,value in parts[label].items():assert word(0xa79+port*0x104+field)==value,(label,hex(field),hex(word(0xa79+port*0x104+field)),hex(value))
 e.save(out/('-'.join(labels)+'-match.state'));e.image(out/('-'.join(labels)+'-match.png'))
 e.run(300,['left','x']);e.run(120);matches.append({'players':labels,'head_and_part_checks':True,'frames_after_intro':660})
 print('PASS match',labels,flush=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
canvas=Image.new('RGB',(768,3*372),(23,26,31));draw=ImageDraw.Draw(canvas);recording=[];actions=[]
for row,(label,title,match,port)in enumerate([('hhh','TRIPLE H','hhh-undertaker',0),('mankind','MANKIND','mankind-austin',0),('undertaker','THE UNDERTAKER','hhh-undertaker',1)]):
 e.load(out/(match+'-match.state'));e.run(1);dual(88,['right'] if port==0 else ['left'],port);dual(28,['up'],port);e.run(10);e.save(out/(label+'-center.state'))
 for col,direction in enumerate(['down','up','left','right']):
  e.load(out/(label+'-center.state'));e.run(1)
  for frame in range(45):
   dual(1,[direction,'x'],port)
   if frame%3==0:recording.append(e.frame().resize((512,448),Image.Resampling.NEAREST))
   if frame==19:
    x=word(0xa79+port*0x104)-word(0xfa3);y=word(0xa7d+port*0x104)-word(0xfa5)
    im=e.frame();im.save(out/(label+'-run-'+direction+'.png'))
    crop=im.crop((x-22,y-76,x+22,y+4)).resize((176,320),Image.Resampling.NEAREST)
    canvas.paste(crop,(col*192+8,row*372+40));draw.text((col*192+8,row*372+10),title if col==0 else '',font=font,fill='white')
    draw.text((col*192+8,row*372+354),'Koşu karesi '+str(col+1),font=font,fill='white')
  actions.append(label+':run-'+direction)
 for key in ['a','b','y','l']:
  e.load(out/(label+'-center.state'));e.run(1);start=np.asarray(e.frame()).copy();dual(4,[key],port);e.run(12)
  assert not np.array_equal(start,np.asarray(e.frame())),(label,key)
  actions.append(label+':'+key)
canvas.save(out/'reference-trio-in-game-views.png')
recording[0].save(out/'reference-trio-gameplay.gif',save_all=True,append_images=recording[1:],duration=50,loop=0,disposal=2)
# A longer CPU bout exercises the new custom body parts in ordinary AI actions.
e.load(out/'options.state');e.run(1);tap('right');tap('right');tap('start');e.run(450);cursor(2);tap('b');tap('b');cursor(4);tap('b');tap('b');tap('start');e.run(450);tap('b');e.run(900)
assert ram()[0x8000:0x9800]==heads['hhh'] and ram()[0xa000:0xb800]==heads['mankind']
start=np.asarray(e.frame()).copy();e.run(3600);assert not np.array_equal(start,np.asarray(e.frame()));e.image(out/'hhh-mankind-cpu.png')
report={'rom_sha256':hashlib.sha256(rom).hexdigest(),'core':'Snes9x 1.62.3 libretro','cold_empty_sram':True,
 'selected':selected,'matches':matches,'custom_head_bytes_and_part_pointers_verified':True,
 'other_81_native_profiles_unchanged':True,'austin_rock_art_unchanged':True,'moves_abilities_unchanged':True,
 'scripted_actions':actions,'cpu_match_frames_after_intro':3600,'page_counts':[16,16,16,16,16,4],
 'limitations':['Dream Match tested; other modes and every move interaction not exhaustively verified.',
 'Tattoos and tiny costume emblems are approximations.','Selection portraits retain previous beta artwork.',
 'Only the first five appearances have individual reference revisions.']}
(out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS five-character regression and new trio gameplay',flush=True)
