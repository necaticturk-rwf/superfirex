"""Prepare compact canonical body/leg views for native-pose retargeting."""
from pathlib import Path
import json,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build_reference_trio import decode
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'assets/full-roster-v1';REF=ROOT/'assets/roster-references'
r=(ROOT/'Super Fire Pro Wrestling X Premium (Japan) [T-En by Sydra v7].sfc').read_bytes();spec=json.loads((A/'specs.json').read_text());rows=spec['rows'];jobs=[j for j in json.loads((A/'generation-jobs.json').read_text())if j['kind']=='heads']
neutral=np.array([(0,0,0),(32,24,16),(136,72,40),(208,136,88),(248,192,144),(16,16,16),(56,40,24),(248,192,144),(96,104,112),(184,192,200),(64,72,88),(128,144,160),(208,216,224),(24,24,32),(56,56,64),(232,232,232)],dtype='uint8')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
for start in range(0,len(rows),3):
 members=rows[start:start+3];im=Image.new('RGB',(128,len(members)*64));refs=Image.new('RGB',(len(members)*320,400),(24,27,32));draw=ImageDraw.Draw(refs)
 for i,row in enumerate(members):
  large=row['silhouette']=='XL';short_names={'Christian','Billy Gunn','Booker T','Jeff Jarrett','Perry Saturn','Kurt Angle','Rob Van Dam','Owen Hart','Mark Henry','Vader','Raven','Tazz','Rhyno','Al Snow','Funaki'}; mode=2 if row['target_name']in short_names else 0 if row['kind']=='trunks' else 1; long=mode==1; row['leg_mode']=mode
  thigh=struct.unpack_from('<H',r,0x1abda+2*((8 if large else 0)+mode))[0]
  lower=0xfcdc if long else 0xfc70
  row['thigh_template_pointer']=thigh;row['lowerleg_template_pointer']=lower
  for part,ptr in enumerate([row['torso_template_pointer'],row['hips_template_pointer'],thigh,lower]):
   off=(ptr<<8)-0xc00000;arr=decode(r[off:off+0x4000])[:16,:128]
   im.paste(Image.fromarray(neutral[arr]),(0,i*64+part*16))
  pic=Image.open(REF/row['reference_file']).convert('RGB');pic.thumbnail((312,360));refs.paste(pic,(i*320+(320-pic.width)//2,35));draw.text((i*320+6,5),str(i+1)+': '+row['target_name'],font=font,fill='white')
 label='canonical-'+str(start//3).zfill(2);path=A/'inputs'/(label+'.png');im.resize((768,len(members)*384),Image.Resampling.NEAREST).save(path);ref=A/'inputs'/(label+'-refs.png');refs.save(ref)
 desc=' '.join(f"BLOCK {i+1}, rows {i*4+1}-{(i+1)*4}: {row['target_name']}: {row['outfit_description']}."for i,row in enumerate(members))
 prompt=f'''Edit FIRST image, technical SNES sports sprite textures; SECOND shows the matching labeled adult professional wrestlers. Return EXACTLY 8columns by{len(members)*4}rows with uniform16x16 cells scaled up, solid pure BLACK background, NO gutters, labels or grid. {len(members)} CHARACTER BLOCKS stacked vertically, FOUR rows per wrestler. Within EACH block: ROW1 =8 disconnected CHEST-only patches; ROW2 =8 ABDOMEN/WAIST-only patches; ROW3 =8 UPPER-LEG/THIGH-only patches; ROW4 =8 LOWER-LEG/KNEE/BOOT-shaft patches. These are separate costume pieces, NOT full figures. NEVER add heads, hair, faces, hands or extra limbs to chest/waist patches. Keep source silhouette/size/anchor for every piece. Preserve each row's original facing sequence: front,3/4front,side,3/4back,back,front,3/4front,side. Do not replace rear views with fronts. Match reference clothing colors and bold motifs; tiny logos become simple pixel shapes. Bare chests stay skin; closed shirts cover chest AND upper abdomen above trousers, no accidental open belly or suspenders. Upper legs carry the reference trouser/tights patterns. Knees and boots match reference colors, no unwanted long white shin stripe on black boots. Pixel art, simple broad16-color shading, all cells isolated. {desc}'''
 jobs.append(dict(label=label,kind='canonical',members=[row['slug']for row in members],input=str(path),reference=str(ref),prompt=prompt))
(A/'specs.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n');(A/'generation-jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2)+'\n');print('Canonical jobs',len(jobs))
