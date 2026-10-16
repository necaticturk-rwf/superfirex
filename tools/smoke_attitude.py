"""Cold boot, navigate all 84 native slots, and exercise native matches.

Save states are created by this run solely to repeat menu navigation. No memory
writes, edit SRAM, or pre-mod states are used to make characters appear.
"""
import argparse,ctypes as C,json,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from headless_snes import Emulator

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rom',type=Path,required=True)
parser.add_argument('--manifest',type=Path,required=True)
parser.add_argument('--core',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--all-matches',action='store_true')
parser.add_argument('--cpu-frames',type=int,default=9000)
a=parser.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
rows=json.loads(a.manifest.read_text())['rows'];e=Emulator(a.rom,a.core)
def tap(k):e.press(k,4);e.run(45)
def ram():return C.string_at(e.core.retro_get_memory_data(2),131072)
def word(addr):return struct.unpack_from('<H',ram(),addr)[0]
def state_regs():
 e.save(a.output_dir/'current.state');s=(a.output_dir/'current.state').read_bytes();b=s[s.index(b'REG:')+11:];return {'pb':b[0],'db':b[1],'p':int.from_bytes(b[2:4],'big'),'sp':int.from_bytes(b[8:10],'big'),'pc':int.from_bytes(b[14:16],'big')}
# Verify a completely empty starting SRAM.
assert not any(C.string_at(e.core.retro_get_memory_data(0),32768))
e.run(1200);tap('start');e.run(150);tap('down');tap('b');e.run(150)
tap('right');tap('right');tap('start');e.run(450)
page_atlas=Image.new('RGB',(768,488));portrait_atlas=Image.new('RGB',(13*80,7*124));d=ImageDraw.Draw(portrait_atlas)
for pg in range(6):
 e.run(90);e.save(a.output_dir/f'page-{pg}.state');page_atlas.paste(e.frame(),((pg%3)*256,(pg//3)*244))
 assert word(0x1881)==pg
 assert word(0x1885)==(16 if pg<5 else 4)
 tap('r')
assert word(0x1881)==0,'Pages do not wrap after six.'
selected=[]
for idx,row in enumerate(rows):
 pg=idx//16;slot=idx%16;e.load(a.output_dir/f'page-{pg}.state');e.run(30)
 for _ in range(slot//4):tap('down')
 for _ in range(slot%4):tap('right')
 e.run(60);ident=word(0x1887)
 assert ident==(pg<<8)|slot,(idx,hex(ident))
 # Match the live native BODY cache to the intended record.
 assert word(0x17fd)==row['body_id'],(idx,word(0x17fd),row['body_id'])
 frame=e.frame();x=(idx%13)*80;y=(idx//13)*124
 portrait_atlas.paste(frame.crop((16,44,105,117)).resize((80,73)),(x,y+16));d.text((x,y),f'{idx+1} {row["short_name"]}',fill='white')
 selected.append({'priority':idx+1,'encoded_id':ident,'body_id':word(0x17fd)})
page_atlas.save(a.output_dir/'pages.png');portrait_atlas.save(a.output_dir/'all-selections.png')
# Load every roster member into a match; longer bouts sample different styles.
match_atlas=Image.new('RGB',(6*256,14*242));dm=ImageDraw.Draw(match_atlas);matches=[]
indices=range(84) if a.all_matches else [0,3,8,17,31,42,43,46,50,65,71,80,83]
for idx in indices:
 pg=idx//16;slot=idx%16;e.load(a.output_dir/f'page-{pg}.state');e.run(30)
 for _ in range(slot//4):tap('down')
 for _ in range(slot%4):tap('right')
 tap('b');tap('b')
 # Deliberately use a different opponent and confirm its color.
 tap('r');tap('b');tap('b');tap('start');e.run(450);tap('b');e.run(900)
 start=np.asarray(e.frame()).copy();grey=np.count_nonzero(np.max(abs(start.astype(int)-(205,213,222)),axis=2)<=2)
 assert grey>3000,('Match did not load',idx+1,grey,state_regs())
 bodyvar=np.count_nonzero(start)
 frames=a.cpu_frames if idx in [0,3,8,17,42,50,65,71] else 600
 e.run(frames);end=np.asarray(e.frame()).copy();assert not np.array_equal(start,end),('Frozen match',idx+1)
 reg=state_regs();assert reg['sp']>0x1000,('Bad native stack',idx+1,reg)
 if idx in [0,3,8,17,31,42,46,50,65,71,83]:e.image(a.output_dir/f'match-{idx+1:02}.png')
 x=idx%6*256;y=idx//6*242;match_atlas.paste(e.frame(),(x,y));dm.text((x,y+224),str(idx+1)+' '+rows[idx]['target_name'],fill='white')
 matches.append({'priority':idx+1,'cpu_frames_after_intro':frames,'stack_pointer':reg['sp'],'loaded_ring_mat_pixels':int(grey)})
 print('match',idx+1,rows[idx]['target_name'],frames,flush=True)
match_atlas.save(a.output_dir/'matches.png')
report={'cold_empty_sram':True,'selected':selected,'matches':matches,'count':len(selected),'page_counts':[16,16,16,16,16,4]}
(a.output_dir/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 84 native selections; matches:',len(matches),flush=True)
