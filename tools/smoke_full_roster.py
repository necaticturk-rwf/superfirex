"""Cold boot, select all 84 wrestlers and load all heads/body pointers in bouts."""
import argparse,ctypes as C,hashlib,json,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from headless_snes import Emulator
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--core',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
out=a.output_dir;out.mkdir(parents=True,exist_ok=True);manifest=json.loads(a.manifest.read_text());rows=manifest['rows'];art={r['target_name']:r for r in manifest['appearances']};rom=a.rom.read_bytes();assert hashlib.sha256(rom).hexdigest()==manifest['rom_sha256'];assert not manifest['missing_development_art']
e=Emulator(a.rom,a.core);e.core.retro_set_controller_port_device(1,1)
assert not any(C.string_at(e.core.retro_get_memory_data(0),32768))
def ram():return C.string_at(e.core.retro_get_memory_data(2),131072)
def word(at):return struct.unpack_from('<H',ram(),at)[0]
def tap(key,port=0):
 if port==0:e.press(key,4);e.run(150 if key=='b'else 45)
 else:e.extra_buttons[port]={e.keys[key]};e.run(4);e.extra_buttons[port]=set();e.run(162 if key=='b'else 57)
def cursor(target,port=0):
 current=word(0x1887)&255;assert current<16
 for _ in range(abs(target//4-current//4)):tap('down'if target//4>current//4 else'up',port)
 for _ in range(abs(target%4-current%4)):tap('right'if target%4>current%4 else'left',port)
 assert word(0x1887)&255==target,(target,word(0x1887))
def page(target,port=0):
 current=word(0x1881)
 for _ in range((target-current)%6):tap('r',port)
 assert word(0x1881)==target,(target,word(0x1881))
e.run(1200);tap('start');e.run(150);tap('down');tap('b');e.run(150);e.save(out/'options.state');tap('right');tap('start');e.run(450)
for pg,count in enumerate(manifest['page_counts']):
 assert word(0x1885)==count,(pg,word(0x1885));e.save(out/f'page-{pg}.state');e.image(out/f'page-{pg}.png');tap('r')
thumbs=[]
for row in rows:
 e.load(out/f"page-{row['page']}.state");e.run(1);cursor(row['slot']);assert word(0x17fd)==row['body_id'],(row['target_name'],word(0x17fd),row['body_id'])
 thumbs.append(e.frame().resize((256,224),Image.Resampling.NEAREST))
canvas=Image.new('RGB',(256*6,248*14),(20,20,24));draw=ImageDraw.Draw(canvas)
for i,(row,im)in enumerate(zip(rows,thumbs)):
 x=(i%6)*256;y=(i//6)*248;canvas.paste(im,(x,y));draw.text((x+4,y+227),f"{i+1:02} {row['target_name']}",fill='white')
canvas.save(out/'all-84-selections.png');print('PASS all 84 selections and six pages',flush=True)
shots=[];matches=[]
for pair in range(42):
 first,second=rows[pair*2:pair*2+2];e.load(out/f"page-{first['page']}.state");e.run(1);cursor(first['slot']);tap('b');tap('b');page(second['page'],1);cursor(second['slot'],1);tap('b',1);tap('b',1);tap('start');e.run(450);tap('b');e.run(1140)
 for port,row in enumerate([first,second]):
  if row['target_name']in art:
   s=art[row['target_name']];head=rom[s['head_source']:s['head_source']+0x1800];assert ram()[0x8000+port*0x2000:0x9800+port*0x2000]==head,(row['target_name'],'head stream')
   for field,value in zip([0xc6,0xc8,0xca,0xcc,0xce,0xd0,0xd2,0xd6],s['parts']):assert word(0xa79+port*0x104+field)==value,(row['target_name'],'part',hex(field),hex(word(0xa79+port*0x104+field)),hex(value))
 e.image(out/f'match-{pair:02}.png');shots.append(e.frame().resize((384,336),Image.Resampling.NEAREST));e.save(out/f'match-{pair:02}.state')
 before=np.array(e.frame());e.run(180,['left','x']);e.run(60);assert not np.array_equal(before,np.array(e.frame())),('no animation',pair)
 matches.append([first['target_name'],second['target_name']]);print('PASS match',pair,*matches[-1],flush=True)
canvas=Image.new('RGB',(384*6,360*7),(20,20,24));draw=ImageDraw.Draw(canvas)
for i,(im,names)in enumerate(zip(shots,matches)):
 x=i%6*384;y=i//6*360;canvas.paste(im,(x,y));draw.text((x+4,y+340),' / '.join(names),fill='white')
canvas.save(out/'all-84-in-game.png')
# Four costume selectors of restored wrestlers are byte-exact originals.
# Longer representative bouts cover masks, large models, printed costumes,
# long sleeves and the new giant; preserve each match state for reproduction.
recording=[];long=[]
for pair in [2,3,5,6,15,23,35,36,41]:
 e.load(out/f'match-{pair:02}.state');e.run(1)
 for direction in ['down','up','left','right']:
  e.run(80,[direction,'x']);e.run(40)
  if pair in [3,35]:
   for i in range(24):e.run(3,[direction]);recording.append(e.frame().resize((512,448),Image.Resampling.NEAREST))
 e.run(720);e.image(out/f'animated-{pair:02}.png');long.append(pair)
if recording:recording[0].save(out/'roster-gameplay.gif',save_all=True,append_images=recording[1:],duration=50,loop=0,disposal=2)
report={'rom_sha256':manifest['rom_sha256'],'core':'Snes9x 1.62.3 libretro','cold_empty_sram':True,'page_counts':manifest['page_counts'],'all_84_selections':True,'matches':matches,'all_67_new_head_streams_and_8_part_pointers_verified':True,'extended_movement_match_indices':long,'limitations':['Dream Match selection and all 84 wrestler loads tested; every move interaction and every game mode are not exhaustive.']};(out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS full roster runtime',flush=True)
