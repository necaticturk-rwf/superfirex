"""Prepare per-character specs and grouped native sprite editing sheets."""
from pathlib import Path
import json,re,struct,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build_reference_trio import decode
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'assets/full-roster-v1';REF=ROOT/'assets/roster-references';A.mkdir(exist_ok=True)
original=(ROOT/'Super Fire Pro Wrestling X Premium (Japan) [T-En by Sydra v7].sfc').read_bytes()
plan=json.loads((ROOT/'assets/attitude/profiles.json').read_text())['rows'];native=json.loads((ROOT/'build/attitude-native-beta/manifest.json').read_text())['rows']
restored_ranks={12,32,42,43,44,45,46,80,81,82,83,84}
notes={}
for line in (A/'appearance-notes.txt').read_text().splitlines():
 name,skin,hair,head,outfit,primary,secondary,accent,kind=line.split('|')
 notes[name]=dict(skin=skin,hair=hair,head_description=head,outfit_description=outfit,primary=primary,secondary=secondary,accent=accent,kind=kind)
def norm(s):return re.sub('[^a-z0-9]','',s.lower().replace('’',"'"))
alias={'thehurricane':'kurrgan','sychosid':'psychosid','diamonddallaspage':'diamondallaspage','bigbossman':'bigbossman'}
paths={norm(p.stem):p for p in REF.iterdir()}
colors={'black':[(8,8,16),(24,24,32),(56,56,64)],'white':[(144,144,152),(200,200,208),(240,240,232)],
 'red':[(104,8,16),(184,16,24),(240,40,40)],'blue':[(16,24,88),(32,56,160),(56,96,224)],
 'green':[(24,64,8),(48,152,16),(96,232,32)],'cyan':[(8,72,80),(16,152,176),(72,224,240)],
 'pink':[(112,8,64),(200,24,136),(248,80,192)],'purple':[(48,16,88),(88,32,152),(144,72,216)],
 'gold':[(112,72,16),(184,136,40),(240,200,88)],'yellow':[(136,112,8),(216,192,24),(248,232,72)],
 'brown':[(40,24,16),(80,48,32),(128,80,48)],'grey':[(56,64,72),(104,112,120),(176,184,192)],
 'blond':[(80,48,16),(160,112,40),(224,184,96)],'bleached':[(136,112,64),(208,192,136),(248,232,176)]}
skins={'fair':[(136,72,40),(208,136,88),(248,192,144)],'tan':[(112,56,24),(184,112,64),(232,168,112)],
 'brown':[(88,40,16),(144,80,40),(200,128,72)],'dark':[(56,24,16),(104,56,32),(160,104,64)],
 'pale':[(112,96,88),(184,168,152),(232,216,200)]}
hairs={'black':[(8,8,8),(40,32,24)],'brown':[(40,24,16),(104,64,32)],'blond':[(104,72,24),(200,160,72)],
 'bleached':[(136,112,64),(232,216,160)],'red':[(88,24,16),(184,64,24)],'gold':[(96,64,16),(224,184,72)]}
bottom_overrides={'Bret Hart':'pink','Rob Van Dam':'white','Road Dogg':'black','Jeff Hardy':'black','Matt Hardy':'blue',
 'Bubba Ray Dudley':'red','D-Von Dudley':'red','D’Lo Brown':'black','Brian Pillman':'red','Raven':'blue',
 'Terry Funk':'red','Al Snow':'black','The Godfather':'green','Gangrel':'black','Spike Dudley':'white',
 'Steven Richards':'brown','Bull Buchanan':'black','Funaki':'blue','Viscera':'black','Mideon':'green'}
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
rows=[]
for record in native:
 rank=record['priority']
 if rank in restored_ranks or rank<=5:continue
 name='Kurrgan'if rank==67 else record['target_name'];s=notes[name];key=alias.get(norm(name),norm(name));ref=paths[key]
 row={**record,**s,'target_name':name,'reference_file':ref.name,'slug':norm(name),'head_model':128+len(rows),'resource_id':0x180+len(rows)}
 sk=skins[s['skin']];hp=hairs[s['hair']]
 if name=='Goldust':sk=colors['gold']
 if name=='Kane':sk=colors['red']
 pc=colors[s['primary']];bc=colors[bottom_overrides.get(name,s['primary'])]
 # Two independent accent colors, plus fixed neutral white, fit native4bpp.
 line=[colors[s['secondary']][-1],colors[s['accent']][-1]]
 row['palette_rgb']=[(0,0,0),(32,24,16),*sk,*hp,sk[-1],*line,*pc,bc[0],bc[-1],(232,232,232)]
 row['bottom_color']=bottom_overrides.get(name,s['primary'])
 desc=s['outfit_description'];boot='black'
 for candidate in ['white','red','blue','gold']:
  if re.search(r'\b'+candidate+r'(?: mid-high| tall| high)? boots',desc):boot=candidate
 row['boot_color']=boot
 row['knee_color']='red'if'red knee'in desc else 'white'if'white knee'in desc else 'blue'if'blue knee'in desc else 'black'
 # Profile chest/abdomen geometry from the prior semantic plan.
 source=plan[rank-1];row['silhouette']=source['silhouette']
 rows.append(row)
assert len(rows)==67 and len(notes)==67
(A/'specs.json').write_text(json.dumps({'rows':rows,'restored_ranks':sorted(restored_ranks),'reference_count':68},ensure_ascii=False,indent=2)+'\n')
(A/'inputs').mkdir(exist_ok=True);(A/'generated').mkdir(exist_ok=True)
neutral=np.array([(0,0,0),(32,24,16),(136,72,40),(208,136,88),(248,192,144),(16,16,16),(56,40,24),(248,192,144),
 (96,104,112),(184,192,200),(64,72,88),(128,144,160),(208,216,224),(24,24,32),(56,56,64),(232,232,232)],dtype='uint8')
def sprite(data,pal=neutral):return Image.fromarray(pal[decode(data)])
def refsheet(members):
 im=Image.new('RGB',(len(members)*320,400),(24,27,32));d=ImageDraw.Draw(im)
 for i,row in enumerate(members):
  pic=Image.open(REF/row['reference_file']).convert('RGB');pic.thumbnail((312,360));im.paste(pic,(i*320+(320-pic.width)//2,35));d.text((i*320+6,5),str(i+1)+': '+row['target_name'],font=font,fill='white')
 return im
jobs=[]
for start in range(0,len(rows),3):
 members=rows[start:start+3];canvas=Image.new('RGB',(128,len(members)*96))
 for index,row in enumerate(members):
  hd=row['head_description'];template='austin'if any(x in hd for x in ['bald','shaved'])or row['target_name']=='Goldust'else'hhh'if any(x in hd for x in ['long','dreadlocks','curly'])else'rock'
  folder='reference-trio-v1'if template=='hhh'else'reference-pair-v1'
  data=(ROOT/f'assets/{folder}/{template}-heads-baseline.bin').read_bytes();canvas.paste(sprite(data,np.array(row['palette_rgb'],dtype='uint8')),(0,index*96))
 label='heads-'+str(start//3).zfill(2);path=A/'inputs'/(label+'.png');canvas.resize((768,len(members)*576),Image.Resampling.NEAREST).save(path)
 rp=A/'inputs'/(label+'-refs.png');refsheet(members).save(rp)
 descriptions=' '.join(f"Rows {i*6+1}-{(i+1)*6}: {row['target_name']}. {row['head_description']}."for i,row in enumerate(members))
 prompt=f'''Edit FIRST image, a technical SNES head atlas. SECOND image contains labeled reference wrestlers. Return exactly8 columns by{len(members)*6} rows of tiny16x16 head cells scaled up, solid pure black background, no gutters, names or grid lines. There are {len(members)} separate wrestler blocks stacked vertically, each8x6=48 HEAD VIEWS. Preserve every cell's original neck anchor, facing, tilt and outline dimensions; heads only, no torsos or limbs. Never replace rear/side views with repeated frontal portraits. Bold readable pixel-art facial features, restrained16-color SNES style. Match each correct reference's face, facial hair, hair and masks: {descriptions} Keep EACH wrestler within its six-row section; preserve all48 original head angles per wrestler.'''
 jobs.append(dict(label=label,kind='heads',members=[r['slug']for r in members],input=str(path),reference=str(rp),prompt=prompt))
for start in range(0,len(rows),2):
 members=rows[start:start+2];canvas=Image.new('RGB',(len(members)*128,512))
 for index,row in enumerate(members):
  size={'S':0,'M':1,'L':2,'XL':3}[row['silhouette']]
  kind=row['kind'];outfit=0 if kind in ['trunks','tights','shorts','jeans']else 1 if kind in ['singlet','vest']else 2
  torso=struct.unpack_from('<H',original,0x1ab9a+2*(size*4+outfit))[0]
  pants=0 if kind in ['trunks','shorts']else 3 if kind in ['singlet','suit','shirt','vest','uniform']else 1
  hips=struct.unpack_from('<H',original,0x1abba+2*(size*4+pants))[0]
  for y,ptr in [(0,torso),(256,hips)]:
   data=original[(ptr<<8)-0xc00000:(ptr<<8)-0xc00000+0x4000]
   canvas.paste(sprite(data),(index*128,y))
  row['torso_template_pointer']=torso;row['hips_template_pointer']=hips
 label='body-'+str(start//2).zfill(2);path=A/'inputs'/(label+'.png');canvas.resize((len(members)*512,2048),Image.Resampling.NEAREST).save(path)
 rp=A/'inputs'/(label+'-refs.png');refsheet(members).save(rp)
 descriptions=' '.join(f"COLUMN BLOCK {i+1} ({'left'if i==0 else'right'}): {row['target_name']}: {row['outfit_description']}."for i,row in enumerate(members))
 prompt=f'''TECHNICAL CLOTHING TEXTURE EDIT. FIRST image contains {len(members)} vertical character columns, each128px wide. Each column has TWO separate8-column x16-row atlases stacked: TOP HALF is CHEST patches only, BOTTOM HALF is ABDOMEN/TRUNK-WAIST patches only. SECOND image contains the corresponding labeled reference wrestlers. Return ONLY edited first technical atlas, exactly{len(members)*8} columns by32 rows, uniform16x16 cells scaled up, pure black background, no gutters, labels or grid. Preserve EACH native patch's silhouette, facing, center and joint anchors in every cell. These are DISCONNECTED CLOTHING/SKIN TEXTURES, never full characters. DO NOT ADD HEADS, HAIR, FACES, ARMS, HANDS OR LEGS. Tops end at headless neck stubs, bottoms end at leg stubs. Maintain chest/abdomen-only geometry. In basic first five rows native views are front,3/4front,side,3/4back,back,front,3/4front,side. Keep back-only graphics on backs. Use bold simple SNES pixel costume details matching reference. For bare chests preserve muscular skin; for shirts cover chest AND UPPER ABDOMEN with closed shirt fabric above proper trouser waistband, no unwanted bare belly/open straps. Singlets continue over belly to shorts/tights waist. No writing outside patches; tiny logos should be simple shapes. {descriptions}'''
 jobs.append(dict(label=label,kind='body',members=[r['slug']for r in members],input=str(path),reference=str(rp),prompt=prompt))
(A/'specs.json').write_text(json.dumps({'rows':rows,'restored_ranks':sorted(restored_ranks),'reference_count':68},ensure_ascii=False,indent=2)+'\n')
(A/'generation-jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2)+'\n')
print('Prepared',len(rows),'wrestlers;',len(jobs),'head/body image jobs')
