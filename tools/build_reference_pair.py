"""Build reference-driven Austin/Rock artwork on the native 84-person beta.

Custom head graphics cover all 48 views. Part edits retain the original sprite
silhouettes and frame indexing. No SRAM or runtime RAM patch is distributed.
"""
from pathlib import Path
import argparse,hashlib,json,struct
from collections import deque
import numpy as np
from PIL import Image
from ring_tiles import tile,write_tile,rgb5
from build_undertaker import ips

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--base-rom',type=Path,default=ROOT/'build/attitude-native-beta/raw-attitude-84-native-beta.sfc')
p.add_argument('--output-dir',type=Path,default=ROOT/'build/reference-pair-v1')
p.add_argument('--heads-only',action='store_true',help='Development preview without new arm/trunk art')
a=p.parse_args();base=a.base_rom.read_bytes();assert hashlib.sha256(base).hexdigest()=='77aadb605a61430b065eafa5bcb33a52dac37ca627a6a99533949b9b9f695298'
r=bytearray(base);assets=ROOT/'assets/reference-pair-v1';manifest=json.loads((ROOT/'build/attitude-native-beta/manifest.json').read_text());rows=manifest['rows']
def put(addr,data):r[addr:addr+len(data)]=data

def rgb555(rgb):return sum(((int(v)*31+127)//255)<<shift for v,shift in zip(rgb,[0,5,10]))

COLORS={
 'austin':{'skin':[(136,72,40),(208,136,88),(248,192,144)],'hair':[(40,24,12),(80,48,24)]},
 'rock':{'skin':[(112,56,24),(184,112,64),(232,168,112)],'hair':[(8,8,8),(40,40,40)]}}

def palette(label):
 spec=COLORS[label]
 return np.array([(0,0,0),(48,32,16),*spec['skin'],*spec['hair'],spec['skin'][-1],(112,116,124),(192,196,204),(40,16,80),(80,40,136),(216,176,48),(16,16,24),(48,48,56),(232,232,232)])

def decode(data):
 return np.block([[tile(data,y*16+x) for x in range(16)]for y in range(len(data)//32//16)])

def encode(indices):
 data=bytearray(indices.size//2)
 for y in range(indices.shape[0]//8):
  for x in range(16):write_tile(data,y*16+x,indices[y*8:y*8+8,x*8:x*8+8])
 return bytes(data)

def cells(image_path,rows):
 im=Image.open(image_path).convert('RGB')
 for row in range(rows):
  for col in range(8):
   yield np.asarray(im.crop((round(col*im.width/8),round(row*im.height/rows),round((col+1)*im.width/8),round((row+1)*im.height/rows))).resize((16,16),Image.Resampling.LANCZOS)).astype(np.int32)

def outside_mask(rgb):
 # Flood only background connected to the cell boundary: dark eyes and mouths
 # remain opaque even when a generated image uses pure black for them.
 dark=rgb.max(axis=2)<15;outside=np.zeros((16,16),bool);queue=deque()
 for x in range(16):
  for y in [0,15]:
   if dark[y,x]:outside[y,x]=True;queue.append((y,x))
 for y in range(16):
  for x in [0,15]:
   if dark[y,x] and not outside[y,x]:outside[y,x]=True;queue.append((y,x))
 while queue:
  y,x=queue.popleft()
  for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
   yy,xx=y+dy,x+dx
   if 0<=yy<16 and 0<=xx<16 and dark[yy,xx] and not outside[yy,xx]:outside[yy,xx]=True;queue.append((yy,xx))
 return outside

art_report={}
for label,model,source,resource,displaced in [('austin',8,0xe7e0f,0x50,0x51),('rock',9,0xc0e14,0x1f,0x20)]:
 original=decode((assets/f'{label}-heads-baseline.bin').read_bytes());out=original.copy();pal=palette(label)
 for idx,rgb in enumerate(cells(assets/f'{label}-heads-generated.png',6)):
  # The head's 16x16 cell and neck anchor are retained, including all tilted views.
  mask=outside_mask(rgb);nearest=((rgb[:,:,None,:]-pal[None,None,1:8,:])**2).sum(axis=3).argmin(axis=2)+1;nearest[mask]=0
  out[idx//8*16:idx//8*16+16,idx%8*16:idx%8*16+16]=nearest
 data=encode(out);assert len(data)==0x1800
 # Two adjacent head streams that are not used by any current wrestler supply
 # a 6 KiB raw slot. Redirect the displaced unused model before overwriting.
 assert not any(row['body_id'] in [1,8,9,24]for row in rows)
 neutral=base[0x15b3b8+0x39*8:0x15b3b8+0x39*8+8]
 put(0x15b3b8+displaced*8,neutral);put(source,data)
 desc=(0xc00000+source).to_bytes(3,'little')+struct.pack('<H',0x1800)+bytes([0,0,0x81]);put(0x15b3b8+resource*8,desc)
 (a.output_dir/'art').mkdir(parents=True,exist_ok=True)
 Image.fromarray(pal[out].astype('uint8')).resize((768,576),Image.Resampling.NEAREST).save(a.output_dir/'art'/f'{label}-compiled-heads.png')
 (a.output_dir/'art'/f'{label}-heads.bin').write_bytes(data)
 art_report[label]={'head_model':model,'head_views':48,'changed_head_pixels':int(np.count_nonzero(out!=original))}

# Unique palette slots: verify all old costumes leave these slots unreferenced.
for cat,slot,addr,values in [
 (0,30,0x5dffe+30*6,COLORS['austin']['skin']),
 (0,34,0x5dffe+34*6,COLORS['rock']['skin']),
 (1,73,0x5e0d0+73*4,COLORS['austin']['hair']),
 (1,74,0x5e0d0+74*4,COLORS['rock']['hair']),
 (2,79,0x5e1fc+79*4,[(112,116,124),(192,196,204)]),
 (3,80,0x5e33c+80*6,[(40,16,80),(80,40,136),(216,176,48)])]:
 assert all(base[0x5d07e+face*32+costume*8+cat]!=slot for face in range(104) for costume in range(4))
 put(addr,struct.pack('<'+'H'*len(values),*(rgb555(v)for v in values)))

for rank,model,body,skin,hair in [(1,8,0x81,30,73),(2,9,2,34,74)]:
 row=rows[rank-1];off=row['profile_offset'];r[off+2]=model;r[off+4]=body;r[off+5]=0x12
 # Bare torso, brief trunks, no long tights, knee pads, standard high boots.
 put(off+286,bytes.fromhex('00 10 00')*4)
 selectors=[skin,hair,9 if rank==1 else 79,1 if rank==1 else 80,0,0,1,0]
 for costume in range(4):put(0x5d07e+row['face_id']*32+costume*8,bytes(selectors))

if not a.heads_only:
 # Confirm that no visible wrestler used the four storage slots before this
 # patch. CA/CC are otherwise fixed; lower-limb collections begin after F688.
 recycled={0xefc8,0xf208,0xf308,0xf408}
 for row in rows:
  off=row['profile_offset'];chest=base[off+5]&15;abs_size=base[off+5]>>4
  for costume in range(4):
   gear=base[off+286+costume*3:off+289+costume*3]
   torso=struct.unpack_from('<H',base,0x1ab9a+2*(chest*4+(gear[0]&15)))[0]
   hips=struct.unpack_from('<H',base,0x1abba+2*(abs_size*4+(gear[0]>>4)))[0]
   assert torso not in recycled and hips not in recycled,(row['target_name'],costume,'shared body asset')
 # Three 16 KiB parts slots are unused by the current native roster. Addresses
 # in actor fields contain address >> 8: e.g. F5C8 means F5:C800, not bank C1.
 parts=[('austin-wrists','austin-forearms-b-baseline.bin',0x2fc800,'austin'),
        ('rock-upperarms','austin-forearms-a-baseline.bin',0x320800,'rock'),
        ('rock-forearms','austin-forearms-b-baseline.bin',0x340800,'rock')]
 for label,baseline,dest,pal_label in parts:
  original=decode((assets/baseline).read_bytes());out=original.copy();count=0
  for idx,rgb in enumerate(cells(assets/f'{label}-generated.png',16)):
   yy,xx=idx//8*16,idx%8*16;orig=original[yy:yy+16,xx:xx+16];skin=np.isin(orig,[2,3,4,7])
   if skin.sum()<5:continue
   dark=(rgb.max(axis=2)<95)&(rgb.min(axis=2)<70)&(~outside_mask(rgb))&skin
   # Only equipment color is transferred; native anatomy, silhouette and frame
   # placement remain bit-for-bit identical outside the generated band mask.
   patch=out[yy:yy+16,xx:xx+16];patch[dark]=np.where(rgb[dark].mean(axis=1)>32,14,13);count+=int(dark.sum())
  put(dest,encode(out));art_report[label]={'edited_skin_pixels':count,'source':baseline,'destination':hex(dest)}
  Image.fromarray(palette(pal_label)[out].astype('uint8')).resize((512,1024),Image.Resampling.NEAREST).save(a.output_dir/'art'/f'{label}-compiled.png')
 # Copy the hip animation and transfer artwork only to the original cloth mask.
 original=decode((assets/'rock-hips-baseline.bin').read_bytes());out=original.copy();count=0
 for idx,rgb in enumerate(cells(assets/'rock-trunks-generated.png',16)):
  yy,xx=idx//8*16,idx%8*16;orig=original[yy:yy+16,xx:xx+16];cloth=np.isin(orig,[8,9,10,11,12,13,14])
  if np.isin(orig,[2,3,4,7]).sum()<5:continue
  red,green,blue=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
  purple=(blue>red*1.25)&(blue>green*1.2)&(blue>45)
  gold=(red>95)&(green>65)&(green>red*.5)&(blue<green*.72)
  silver=(abs(red-green)<35)&(abs(green-blue)<35)&(rgb.mean(axis=2)>85)
  colors=np.where(rgb.mean(axis=2)>30,14,13).astype(np.uint8)
  colors[purple]=np.where(blue[purple]>90,11,10);colors[gold]=12;colors[silver]=np.where(rgb.mean(axis=2)[silver]>155,9,8)
  patch=out[yy:yy+16,xx:xx+16];patch[cloth]=colors[cloth];count+=int(np.count_nonzero(patch[cloth]!=orig[cloth]))
 put(0x330800,encode(out));art_report['rock-trunks']={'changed_cloth_pixels':count,'destination':'0x330800'}
 Image.fromarray(palette('rock')[out].astype('uint8')).resize((512,1024),Image.Resampling.NEAREST).save(a.output_dir/'art/rock-trunks-compiled.png')
 # The native part-setup helper is shared by selection and actual matches.
 # Preserve its original register/status contract and return A=EE88 as before.
 stub=bytearray();labels={};branches=[]
 def emit(s):stub.extend(bytes.fromhex(s))
 def branch(op,label):emit(op);branches.append((len(stub),label));stub.append(0)
 def mark(label):labels[label]=len(stub)
 emit('08 5a a9 88 ee 95 d6 a4 be b9 00 00 c9 08 00');branch('d0','rock')
 emit('a9 c8 ef 95 cc');branch('80','done')
 mark('rock');emit('c9 09 00');branch('d0','done')
 emit('a9 08 f2 95 ca a9 08 f4 95 cc a9 08 f3 95 c8')
 mark('done');emit('7a 28 a9 88 ee 6b')
 for at,label in branches:delta=labels[label]-(at+1);assert -128<=delta<=127;stub[at]=delta&255
 assert base[0x10bef:0x10bf5]==bytes.fromhex('a9 88 ee 95 d6 60')
 assert set(base[0x1e500:0x1e500+len(stub)])=={255}
 put(0x1e500,stub);put(0x10bef,bytes.fromhex('22 00 e5 c1 60 ea'))

put(0xffdc,bytes.fromhex('ff ff 00 00'));check=sum(r)&65535;put(0xffdc,struct.pack('<HH',check^65535,check));assert sum(r)&65535==check and len(r)==len(base)
a.output_dir.mkdir(parents=True,exist_ok=True);name='raw-austin-rock-reference-v1';output=a.output_dir/(name+'.sfc');assert output.resolve()!=a.base_rom.resolve();output.write_bytes(r);(a.output_dir/(name+'-from-native-beta.ips')).write_bytes(ips(base,r))
report={'version':name,'heads_only_development':a.heads_only,'base_sha256':hashlib.sha256(base).hexdigest(),'rom_sha256':hashlib.sha256(r).hexdigest(),'modified_roster_ranks':[1,2],'art':art_report,'notes':['Only Austin/Rock are revised; the remaining roster has not been remade.','Trunk logos are miniature pixel approximations, not readable text.','Moves and abilities are retained from the previous native profiles.']}
(a.output_dir/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,indent=2))
(a.output_dir/'README_TR.txt').write_bytes((assets/'README_TR.txt').read_bytes())
