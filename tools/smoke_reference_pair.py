"""Cold-boot verification and real-game capture for the two-character revision."""
import argparse, ctypes as C, hashlib, json, struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from headless_snes import Emulator
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--rom',type=Path,required=True);p.add_argument('--base-rom',type=Path,required=True)
p.add_argument('--base-manifest',type=Path,required=True);p.add_argument('--art-dir',type=Path,required=True)
p.add_argument('--core',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
a=p.parse_args();out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
base=a.base_rom.read_bytes();rom=a.rom.read_bytes();rows=json.loads(a.base_manifest.read_text())['rows']
# Every other native profile and the accepted ring tile sources remain identical.
for row in rows[2:]:
 off=row['profile_offset'];assert rom[off:off+298]==base[off:off+298],row['target_name']
# Only appearance fields may change in the first two records.
for row in rows[:2]:
 off=row['profile_offset'];changed=[i for i in range(298) if rom[off+i]!=base[off+i]]
 assert all(i in [2,4,5] or 286<=i<298 for i in changed)
assert struct.unpack_from('<HH',rom,0xffdc)[0]^struct.unpack_from('<HH',rom,0xffdc)[1]==65535
assert sum(rom)&65535==struct.unpack_from('<H',rom,0xffde)[0]
e=Emulator(a.rom,a.core);e.core.retro_set_controller_port_device(1,1)
assert not any(C.string_at(e.core.retro_get_memory_data(0),32768))
def ram():return C.string_at(e.core.retro_get_memory_data(2),131072)
def word(addr):return struct.unpack_from('<H',ram(),addr)[0]
def tap(k,port=0):
 if port==0:e.press(k,4);e.run(150 if k=='b' else 45)
 else:e.extra_buttons[port]={e.keys[k]};e.run(4);e.extra_buttons[port]=set();e.run(162 if k=='b' else 57)
def dual(n,keys,port):
 if port==0:e.run(n,keys)
 else:e.extra_buttons[port]={e.keys[k] for k in keys};e.run(n);e.extra_buttons[port]=set()
e.run(1200);tap('start');e.run(150);tap('down');tap('b');e.run(150);e.save(out/'options.state')
# The shared part hook is exercised by all 84 selection entries.
tap('start');e.run(450)
for pg in range(6):e.save(out/f'page-{pg}.state');tap('r')
selected=[]
for i,row in enumerate(rows):
 e.load(out/f'page-{i//16}.state');e.run(1)
 for _ in range(i%16//4):tap('down')
 for _ in range(i%4):tap('right')
 expected=8 if i==0 else 9 if i==1 else row['body_id']
 assert word(0x17fd)==expected,(i,word(0x17fd),expected)
 if i<2:e.image(out/('austin-selection.png' if i==0 else 'rock-selection.png'))
 selected.append({'rank':i+1,'body':expected})
print('PASS 84 selection models',flush=True)
# Start a genuine 1P vs 2P match so both characters can be directed independently.
e.load(out/'options.state');e.run(1);tap('right');tap('start');e.run(450)
tap('b');tap('b');tap('right',1);tap('b',1);tap('b',1);tap('start');e.run(450);e.image(out/'versus.png');tap('b');e.run(900);e.run(240)
e.save(out/'pair-match.state');e.image(out/'pair-match.png')
for port,label,address,parts in [(0,'austin',0x8000,{0xcc:0xefc8}),(1,'rock',0xa000,{0xca:0xf208,0xcc:0xf408,0xc8:0xf308})]:
 expected=(a.art_dir/f'{label}-heads.bin').read_bytes();assert ram()[address:address+len(expected)]==expected
 for field,value in parts.items():assert word(0xa79+port*0x104+field)==value,(label,field)
# Four run directions, plus strikes and taunts, all from states made by this ROM.
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
canvas=Image.new('RGB',(768,744),(23,26,31));draw=ImageDraw.Draw(canvas);gif=[];actions=[]
for port,label,title in [(0,'austin','STONE COLD'),(1,'rock','THE ROCK')]:
 e.load(out/'pair-match.state');e.run(1);dual(88,['right'] if port==0 else ['left'],port);dual(28,['up'],port);e.run(10);e.save(out/f'{label}-center.state')
 for col,direction in enumerate(['down','up','left','right']):
  e.load(out/f'{label}-center.state');e.run(1)
  for frame in range(45):
   dual(1,[direction,'x'],port)
   if frame%3==0:gif.append(e.frame().resize((512,448),Image.Resampling.NEAREST))
   if frame==19:
    x=word(0xa79+port*0x104)-word(0xfa3);y=word(0xa7d+port*0x104)-word(0xfa5)
    image=e.frame();image.save(out/f'{label}-run-{direction}.png')
    crop=image.crop((x-22,y-76,x+22,y+4)).resize((176,320),Image.Resampling.NEAREST)
    draw.text((col*192+8,port*372+10),title if col==0 else '',font=font,fill='white')
    canvas.paste(crop,(col*192+8,port*372+40));draw.text((col*192+8,port*372+357),f'Koşu karesi {col+1}',font=font,fill='white')
  actions.append(label+':run-'+direction)
 for button in ['a','b','y','l']:
  e.load(out/f'{label}-center.state');e.run(1);start=np.asarray(e.frame()).copy();dual(4,[button],port);e.run(12)
  assert not np.array_equal(start,np.asarray(e.frame())),(label,button,'no animation')
  actions.append(label+':'+button)
canvas.save(out/'reference-pair-in-game-views.png');gif[0].save(out/'reference-pair-gameplay.gif',save_all=True,append_images=gif[1:],duration=50,loop=0,disposal=2)
# CPU Undertaker match checks that the globally shared hook still handles an
# unrelated native model, while ring graphics are checked by rope_regression.py.
e.load(out/'options.state');e.run(1);tap('right');tap('right');tap('start');e.run(450)
for _ in range(3):tap('right')
tap('b');tap('b');tap('b');tap('b');tap('start');e.run(450);tap('b');e.run(900)
assert word(0xa79+0xd4)==0x7e80
start=np.asarray(e.frame()).copy();e.run(1800);assert not np.array_equal(start,np.asarray(e.frame()));e.image(out/'undertaker-regression.png')
report={'rom_sha256':hashlib.sha256(rom).hexdigest(),'core':'Snes9x 1.62.3 libretro','cold_empty_sram':True,'selected':selected,'custom_head_bytes_verified':True,'custom_arm_and_hip_pointers_verified':True,'other_82_profiles_unchanged':True,'first_two_moves_abilities_unchanged':True,'scripted_actions':actions,'undertaker_cpu_frames':1800,'limitations':['Visual likeness requires user review.','Tiny trunk logos cannot be read as text.','Other 82 appearances have not been redone.','This is a Dream Match check, not exhaustive move or game-mode coverage.']}
(out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS pair runtime and Undertaker regression',flush=True)
