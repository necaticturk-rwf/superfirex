"""Build the native 84-person Attitude roster on the accepted RAW ring v3.

No SRAM or runtime RAM edits are needed by the output ROM. Native body art is
provisional: the separate portraits must not be confused with in-ring sprites.
"""
from pathlib import Path
import argparse
import json,struct,hashlib
import numpy as np
from PIL import Image
from ring_tiles import write_tile, rgb5
from build_undertaker import ips

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-rom',type=Path,default=root/'build/raw-is-war-v3.sfc')
parser.add_argument('--output-dir',type=Path,default=root/'build/attitude-native-beta')
parser.add_argument('--skip-portraits',action='store_true',help='Development only')
args=parser.parse_args()
original=args.base_rom.read_bytes()
assert hashlib.sha256(original).hexdigest()=='f3a6e07c10d3494b398d9c0c0883736f0e47f84f75113bd64adfb2629be62474'
r=bytearray(original)
plan=json.loads((root/'assets/attitude/profiles.json').read_text())['rows']
pool=0x3ff800
string_cache={}
shorts=['AUSTIN','ROCK','HHH','TAKER','MANKIND','KANE','HBK','BRET','ANGLE','JERICHO','BIGSHOW','VINCE','BENOIT','EDDIE','EDGE','CHRISTN','RIKISHI','RVD','BOOKER','X PAC','ROADOGG','BILLY','JEFF','MATT','BUBBA','D VON','FAAROOQ','BRADSHW','SHAMRCK','OWEN','BULLDOG','CHYNA','CACTUS','GOLDUST','JARRETT','HENRY','D LO','VENIS','TEST','BOSSMAN','REGAL','SHANE','LITA','TRISH','SABLE','STEPH','VADER','SID','PILLMAN','RAVEN','TAZZ','RHYNO','DDP','FUNK','BLACKMN','AL SNOW','H HOLLY','CRASH','SCOTTY','SEXAY','GODFTHR','GANGREL','DUDE','MALENKO','SATURN','TAJIRI','HURRCNE','STORM','ALBERT','SPIKE','HAKU','VISCERA','MIDEON','RICHARD','BULL','TAKA','FUNAKI','ESSA','K KWIK','TORI','JACKIE','IVORY','MOLLY','LUNA']
def put(a,b):r[a:a+len(b)]=b
def w(a,n):put(a,struct.pack('<H',n))
def text(s):
 out=[]
 for c in s.upper():
  if c==' ':v=0
  elif c.isdigit():v=0x1d+int(c)
  elif 'A'<=c<='Z':v=ord(c)-26
  else:v=0
  out.append(0x8000+v)
 return struct.pack('<'+'H'*(len(out)+1),*out,65535)
def str_resource(res,s):
 global pool
 b=text(s)
 if s in string_cache:ptr=string_cache[s]
 else:
  if pool>=0x3ff800 and pool+len(b)>0x400000:pool=0x82a65
  assert (0x82a65<=pool and pool+len(b)<=0x834e1) or (0x3ff800<=pool and pool+len(b)<=0x400000)
  ptr=pool;put(ptr,b);pool+=len(b);string_cache[s]=ptr
 put(0x80000+res,(ptr-0x80000).to_bytes(3,'little'))
def splitname(t):
 fixed={'Stone Cold Steve Austin':('STONE COLD','S AUSTIN'),'The Undertaker':('UNDERTAKER',''),'Triple H':('TRIPLE H',''),'Rob Van Dam':('ROB','VAN DAM'),'Bubba Ray Dudley':('BUBBA RAY','DUDLEY'),'D-Von Dudley':('D VON','DUDLEY'),'Grand Master Sexay':('GRAND MSTR','SEXAY'),'Diamond Dallas Page':('DIAMOND','DALLAS PAGE'),'D’Lo Brown':('D LO','BROWN'),'K-Kwik':('K KWIK','')}
 if t in fixed:return fixed[t]
 p=t.rsplit(' ',1);return (p[0],p[1]) if len(p)==2 else(t,'')
sourcemap=json.loads((root/'research/attitude-roster-plan/source-native-map.json').read_text())

# Each native color selector addresses its own shared RGB555 shade table.
color_tables=[(0x5dffe,6,35),(0x5e0d0,4,75),(0x5e1fc,4,80),
              (0x5e33c,6,81),(0x5e522,4,96),(0x5e6a2,4,60),
              (0x5e792,6,93),(0x5e9c0,4,69)]
shades={'black':[(2,2,2),(4,4,4),(7,8,8)],
        'white':[(19,19,20),(25,25,26),(31,31,31)],
        'red':[(10,0,0),(19,1,0),(29,4,2)],
        'blue':[(0,2,10),(0,6,19),(4,13,31)],
        'green':[(0,6,1),(1,15,3),(7,25,9)],
        'pink':[(12,0,7),(22,2,14),(31,9,24)],
        'purple':[(7,0,12),(14,1,22),(24,7,31)],
        'yellow':[(12,7,0),(23,18,0),(31,28,7)],
        'gold':[(10,6,0),(21,16,1),(30,24,7)],
        'brown':[(6,2,0),(12,6,2),(20,12,6)],
        'orange':[(12,3,0),(24,8,0),(31,17,2)],
        'grey':[(4,4,4),(10,10,10),(19,19,19)],
        'blond':[(12,8,2),(20,15,5),(29,24,12)],
        'light':[(17,10,6),(26,16,10),(31,24,18)],
        'dark':[(6,3,2),(12,6,3),(20,12,6)]}

def selector(category,color):
 if category==0 and color=='pale':return 18
 if category==0 and color=='brown':target=[(11,5,2),(18,10,5),(26,18,11)]
 else:target=shades[color]
 base,stride,count=color_tables[category]
 target=np.array(target if stride==6 else [target[0],target[-1]])
 candidates=np.array([rgb5(struct.unpack_from('<'+'H'*(stride//2),original,base+j*stride)) for j in range(count)])
 return int(((candidates-target)**2).sum(axis=(1,2)).argmin())

def cumulative(values):
 assert sum(values)==100 and all(0<=v<=100 for v in values)
 return np.cumsum(values)[:-1].astype(np.uint8).tobytes()

def native_profile(row,old):
 out=bytearray(old)
 template_id=row['cpu']['template_native_id']
 template=original[0x48481+template_id*298:0x48481+(template_id+1)*298]
 out[:280]=template[:280]
 out[0]=old[0]  # Unique portrait and body-palette lookup, independent of head model.
 out[1]=7 if row['priority']==4 else old[1]
 out[2]=row['body_model']
 out[3]=0
 size={'S':(0,0,0),'M':(1,1,1),'L':(2,2,1),'XL':(2,3,3)}[row['silhouette']]
 out[4]=size[0] | (0x80 if row['silhouette']=='XL' else 0)
 out[5]=size[1] | (size[2]<<4)
 skill=row['skills']
 out[6]=skill['style'] | (skill['counter']<<4)
 out[7]=skill['recovery'] | (skill['cut_recovery']<<4)
 out[8]=skill['speed'] | (skill['climb']<<4)
 out[9]=skill['critical'];out[10]=skill['ring_count'];out[11]=skill['teamwork']
 out[12]=6 if row['archetype']=='agile' else 0
 for offset,values in [(13,row['attack']),(18,row['defense'])]:
  assert all(1<=v<=5 for v in values)
  out[offset:offset+len(values)//2]=bytes((values[j]+1)|((values[j+1]+1)<<4) for j in range(0,len(values),2))
 assert len(row['moves'])==57
 struct.pack_into('<57H',out,25,*row['moves'])
 out[139]=row['finisher']['slot']+1
 out[147:149]=cumulative(row['cpu']['walking'])
 out[149:151]=cumulative(row['cpu']['walking'])
 out[187:191]=cumulative(row['cpu']['late_grapple'])
 # SUIT2/long pants is a provisional shirt silhouette, not bespoke sleeve art.
 gear={'trunks':bytes.fromhex('00 00 00'),'tights':bytes.fromhex('10 01 00'),
       'suit':bytes.fromhex('32 01 22'),'shirt':bytes.fromhex('12 01 00')}[row['gear']]
 if 'gear_bytes' in row:gear=bytes(row['gear_bytes'])
 out[286:298]=gear*4
 colors=[row['skin'],row['hair'],'black',row['attire_color'],row['attire_color'],'black','black','black']
 if 'attire_colors' in row:colors[2:]=row['attire_colors']
 selectors=[selector(j,c) for j,c in enumerate(colors)]
 for costume in range(4):put(0x5d07e+old[0]*32+costume*8,bytes(selectors))
 return out,selectors

def portrait(row,face_id):
 page=(row['priority']-1)//16+1;side=2 if page==6 else 4;cell=(row['priority']-1)%16
 im=Image.open(root/f'assets/attitude/portraits/page-{page}-atlas.png').convert('RGB')
 x=cell%side;y=cell//side
 im=im.crop((round(x*im.width/side),round(y*im.height/side),round((x+1)*im.width/side),round((y+1)*im.height/side)))
 im=im.resize((32,32),Image.Resampling.LANCZOS).quantize(colors=14,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
 indices=np.asarray(im,dtype=np.uint8)+1
 palette=np.array(im.getpalette()[:42]).reshape(14,3)
 rgb=(palette.astype(np.uint16)*31+127)//255
 words=rgb[:,0] | (rgb[:,1]<<5) | (rgb[:,2]<<10)
 put(0xf3d44+face_id*28,struct.pack('<14H',*words))
 tiles=bytearray(512)
 for y in range(4):
  for x in range(4):write_tile(tiles,y*4+x,indices[y*8:y*8+8,x*8:x*8+8])
 put(0x70000+face_id*512,tiles)

rows=[]
for i,row in enumerate(plan):
 src=next(x for x in sourcemap if x['source_name']==row['source_name'] and x['source_group']==row['source_group']);enc=src['source_encoded_id'];ptr=src['profile_offset'];p=original[ptr:ptr+298]
 out,selectors=native_profile(row,p);put(ptr,out)
 rec={**row,'source_encoded_id':enc,'profile_offset':ptr,'face_id':p[0],'body_id':out[2],'short_name':shorts[i][:6],'palette_selectors':selectors}
 rows.append(rec)
 first,last=splitname(row['target_name']);first=first[:10];last=last[:10];shorts[i]=shorts[i][:6]
 for res,s in zip(struct.unpack_from('<3H',p,280),[first,last,shorts[i]]):str_resource(res,s)
 if not args.skip_portraits:portrait(row,p[0])
for n in range(104):
 if 0x48481+n*298 not in {x['profile_offset'] for x in rows}:
  for res,t in zip(struct.unpack_from('<3H',original,0x48481+n*298+280),['RESERVE','','RESERV']):str_resource(res,t)
# New six native group lists, in approved priority order.
unused=sorted(set(range(104))-{x['face_id'] for x in rows})
a=next(a for a in unused if a+1 in unused)
pointer_pool=0x48481+a*298;order_pool=pointer_pool+6*16*2
# Point any obsolete native references to a valid retained profile before recycling.
for off in range(0x48209,0x482d9,2):
 old=struct.unpack_from('<H',original,off)[0]
 if old in [pointer_pool&65535,(pointer_pool+298)&65535]:w(off,rows[0]['profile_offset']&65535)
print('reclaimed',a,a+1,hex(pointer_pool))
for g in range(6):
 members=rows[g*16:g*16+16];w(0x481eb+g*2,pointer_pool&65535);w(0x482d9+g*2,order_pool&65535)
 # Pad the last list too: legacy scripted opponents may use the old fifth
 # member of this group, although the new menu correctly exposes only four.
 for j in range(16):
  rec=members[j%len(members)]
  w(pointer_pool,rec['profile_offset']&65535);pointer_pool+=2
  w(order_pool,(g<<8)|(j%len(members)));order_pool+=2
 for base in [0x481cd,0x481dc]:put(base+g,bytes([len(members)]))
 res=struct.unpack_from('<H',original,0x48180+g*2)[0];str_resource(res,f'WWF {g+1:02}')
# Report six groups irrespective of SRAM unlock or edit flags.
assert r[0x29156:0x2915c]==bytes.fromhex('8bf40084abab');put(0x29156,bytes.fromhex('a9060085816b'))
# Keep the existing group-choice arrays: their first six entries are 0..5.
for a in [0x481a0,0x481ae,0x481bd]:assert r[a:a+6]==bytes(range(6))
assert len({p['profile_offset'] for p in rows})==84
put(0xffdc,bytes.fromhex('ffff0000'));n=sum(r)&65535;put(0xffdc,struct.pack('<HH',n^65535,n))
assert sum(r)&65535==n and len(r)==len(original)
args.output_dir.mkdir(parents=True,exist_ok=True)
name='raw-attitude-84-native-beta'
assert (args.output_dir/(name+'.sfc')).resolve()!=args.base_rom.resolve(), 'Output must not overwrite the base ROM.'
(args.output_dir/(name+'.sfc')).write_bytes(r)
(args.output_dir/(name+'-from-raw-v3.ips')).write_bytes(ips(original,r))
report={'status':'beta; native sprite art provisional','base_sha256':hashlib.sha256(original).hexdigest(),
        'rom_sha256':hashlib.sha256(r).hexdigest(),'portraits_applied':not args.skip_portraits,
        'page_counts':[16,16,16,16,16,4],'rows':rows}
(args.output_dir/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
