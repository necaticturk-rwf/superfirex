"""Build the 72-person referenced WWF roster plus 12 restored native wrestlers.

The accepted first five appearances are retained. New art uses custom heads,
canonical costume views retargeted onto native poses, and modular arm/boot gear.
The ROM expands to 8 MiB ExHiROM, supported by stock Snes9x 1.62.3.
"""
from pathlib import Path
import argparse,hashlib,json,struct,csv,io
import numpy as np
from PIL import Image
from build_reference_trio import decode,encode,outside_mask,rgb555
from sprite_retarget import compile_part,sheet_views,split_cells,join_cells
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'assets/full-roster-v1'
BASE_SHA='1a9d07a5aac9170627ad3c46be2b9bc4f5375b7292103c1775b92b0c2a458526'
NAME='raw-attitude-72-reference-v1'
PALETTES=[(0x5dffe,6,35),(0x5e0d0,4,75),(0x5e1fc,4,80),(0x5e33c,6,81),
          (0x5e522,4,96),(0x5e6a2,4,60),(0x5e792,6,93),(0x5e9c0,4,69)]
COLORS={'black':[(8,8,16),(24,24,32),(56,56,64)],'white':[(144,144,152),(200,200,208),(240,240,232)],
 'red':[(104,8,16),(184,16,24),(240,40,40)],'blue':[(16,24,88),(32,56,160),(56,96,224)],
 'gold':[(112,72,16),(184,136,40),(240,200,88)],'grey':[(56,64,72),(104,112,120),(176,184,192)],
 'green':[(24,64,8),(48,152,16),(96,232,32)]}
PLAIN_HIPS={'Big Show','Ken Shamrock','Val Venis','William Regal','Dean Malenko','Sycho Sid'}
PLAIN_LEGS={'Faarooq','Bradshaw','Jeff Hardy','Matt Hardy','Test','Big Boss Man','Diamond Dallas Page',
 'Steve Blackman','Tazz','Rhyno','The Godfather','Gangrel','Dude Love','Viscera','Mideon','Kurrgan','Steven Richards','Bull Buchanan'}
INK_TORSOS={'Bradshaw','Perry Saturn','Albert'}
CUSTOM_BOOTS={'Shawn Michaels','Kurt Angle','Billy Gunn','Jeff Jarrett','Tajiri','TAKA Michinoku','Chris Benoit','Lance Storm','Funaki'}

def digest(data):return hashlib.sha256(data).hexdigest()
def text_bytes(s):
 values=[]
 for c in s.upper():
  v=0 if c==' ' else 0x1d+int(c) if c.isdigit() else ord(c)-26 if 'A'<=c<='Z' else 0
  values.append(0x8000+v)
 return struct.pack('<'+'H'*(len(values)+1),*values,65535)
def original_text(rom,res):
 pos=0x80000+int.from_bytes(rom[0x80000+res:0x80000+res+3],'little');end=pos
 while rom[end:end+2]!=b'\xff\xff':end+=2;assert end-pos<512
 return rom[pos:end+2]
def rgba555(data):
 words=np.frombuffer(data,'<u2').astype(np.uint32)
 return np.stack((words&31,(words>>5)&31,(words>>10)&31),axis=1)*255//31

class Builder:
 def __init__(self,args):
  self.args=args;self.base=args.base_rom.read_bytes();assert digest(self.base)==BASE_SHA
  self.orig=(ROOT/'Super Fire Pro Wrestling X Premium (Japan) [T-En by Sydra v7].sfc').read_bytes()
  self.r=bytearray(self.base)+bytearray([255])*0x400000;self.pos=0x414000;self.allocations=[]
  self.rows=json.loads((ROOT/'build/attitude-native-beta/manifest.json').read_text())['rows']
  self.spec=json.loads((A/'specs.json').read_text());self.restored=set(self.spec['restored_ranks'])
  self.new=self.spec['rows'];self.by_rank={x['priority']:x for x in self.new};self.missing=[]
  self.jobs=json.loads((A/'generation-jobs.json').read_text());self.images={}
  for job in self.jobs:
   for index,slug in enumerate(job['members']):self.images[(slug,job['kind'])]=(A/'generated'/(job['label']+'.png'),index,len(job['members']))
  self.out=args.output_dir;self.art=self.out/'art';self.art.mkdir(parents=True,exist_ok=True)
 def put(self,offset,data):self.r[offset:offset+len(data)]=data
 def word(self,offset,value):struct.pack_into('<H',self.r,offset,value&65535)
 def alloc(self,label,data,head=False):
  self.pos=(self.pos+255)&~255
  if head and (self.pos&65535)+len(data)>=65536:self.pos=(self.pos+65535)&~65535;self.pos+=256
  start=self.pos;end=start+len(data);assert end<=0x7e0000,(label,hex(end),'ExHiROM addressable expansion exhausted')
  self.put(start,data);self.pos=end;self.allocations.append({'name':label,'offset':start,'bytes':len(data)})
  return start
 def name(self,res,data):
  self.name_data[res]=data
 def descriptor(self,res,source,size):self.put(0x410000+res*8,source.to_bytes(3,'little')+struct.pack('<H',size)+bytes([0,0,0x81]))
 def restore(self):
  self.name_data={}
  for row in self.rows:
   if row['priority']not in self.restored:continue
   off=row['profile_offset'];record=self.orig[off:off+298];face=record[0];self.put(off,record)
   for res in struct.unpack_from('<3H',record,280):self.name(res,original_text(self.orig,res))
   self.put(0x70000+face*512,self.orig[0x70000+face*512:0x70000+(face+1)*512])
   self.put(0xf3d44+face*28,self.orig[0xf3d44+face*28:0xf3d44+(face+1)*28])
   self.put(0x5d07e+face*32,self.orig[0x5d07e+face*32:0x5d07e+(face+1)*32])
  # Preserve every original resource descriptor, including ones after 0x180.
  self.put(0x410000,self.base[0x15b3b8:0x15b3b8+0x2000]);self.put(0x60000,bytes.fromhex('00 00 41'))
  source=self.alloc('accepted-undertaker-head-relocation',self.base[0x1e7e0:0x1ffe0],head=True)
  self.descriptor(0x61,source,0x1800)
  # Moving this raw stream frees the expanded model table inside bank81.
  table=bytearray(512)
  for model in range(256):
   resource=struct.unpack_from('<H',self.base,0x1b15e+model*2)[0]if model<108 else 0x8039
   struct.pack_into('<H',table,model*2,resource)
  self.put(0x1e800,table)
  for pos in [0x101dc,0x101fa,0x10218,0x10236,0x108aa,0x108bb,0x108cc,0x108dd,0x10a84,0x10aad,0x10ad6,0x10aff]:
   assert self.base[pos:pos+2]==bytes.fromhex('5e b1');self.put(pos,bytes.fromhex('00 e8'))
  assert self.base[0x10a73:0x10a76]==bytes.fromhex('29 ff 00');self.put(0x10a74,bytes.fromhex('ff 01'))
 def native_parts(self):
  self.native_map={}
  for table,count,size in [(0x1ab9a,16,0x4000),(0x1abba,16,0x4000),(0x1abda,16,0x6c00),(0x1abfa,16,0x6c00),(0x1ac1a,4,0x4000)]:
   for ptr in sorted(set(struct.unpack_from('<'+'H'*count,self.orig,table))):
    offset=(ptr<<8)-0xc00000
    if self.base[offset:offset+size]!=self.orig[offset:offset+size]:
     data=self.orig[offset:offset+size];new=self.alloc('restore-native-part-'+hex(ptr),data)>>8;self.native_map[ptr]=new
   for i,ptr in enumerate(struct.unpack_from('<'+'H'*count,self.orig,table)):
    if ptr in self.native_map:self.word(table+i*2,self.native_map[ptr])
 def palette_slots(self):
  self.locked=[set()for _ in PALETTES]
  for row in self.rows:
   if row['priority']<=5 or row['priority']in self.restored:
    face=self.r[row['profile_offset']]
    for c in range(4):
     for cat in range(8):self.locked[cat].add(self.r[0x5d07e+face*32+c*8+cat])
  self.saved_locked={}
  for cat,(start,step,count)in enumerate(PALETTES):
   for slot in self.locked[cat]:self.saved_locked[(cat,slot)]=bytes(self.r[start+slot*step:start+(slot+1)*step])
 def select(self,cat,colors):
  start,step,count=PALETTES[cat];data=struct.pack('<'+'H'*len(colors),*(rgb555(c)for c in colors));assert len(data)==step
  for i in range(count):
   if self.r[start+i*step:start+(i+1)*step]==data:self.locked[cat].add(i);return i
  available=sorted(set(range(count))-self.locked[cat]);assert available,('No palette slots',cat)
  slot=available[0];self.put(start+slot*step,data);self.locked[cat].add(slot);return slot
 def actor_palette(self,s):
  p=s['palette_rgb'];boot=COLORS[s['boot_color']];knee=COLORS[s['knee_color']]
  colors=[p[2:5],p[5:7],p[8:10],p[10:13],p[13:15],[boot[0],boot[-1]],knee,[boot[0],boot[-1]]]
  slots=[self.select(i,c)for i,c in enumerate(colors)]
  first=np.array([(0,0,0),(49,41,16),*rgba555(struct.pack('<3H',*(rgb555(c)for c in p[2:5]))),
    *rgba555(struct.pack('<2H',*(rgb555(c)for c in p[5:7]))),p[4],*p[8:15],(232,232,232)],dtype=np.int32)
  second=np.array([(0,0,0),(49,41,16),(0,0,0),*p[2:5],p[4],p[4],boot[0],boot[-1],*knee,boot[0],boot[-1],(232,232,232)],dtype=np.int32)
  return slots,first,second
 def heads(self,s,pal):
  path,index,count=self.images[(s['slug'],'heads')]
  if not path.exists():
   self.missing.append(str(path));assert self.args.allow_incomplete,path
   return (ROOT/'assets/reference-pair-v1/austin-heads-baseline.bin').read_bytes()
  im=Image.open(path).convert('RGB');im=im.crop((0,round(index*im.height/count),im.width,round((index+1)*im.height/count)))
  cells=[]
  for y in range(6):
   for x in range(8):
    rgb=np.asarray(im.crop((round(x*im.width/8),round(y*im.height/6),round((x+1)*im.width/8),round((y+1)*im.height/6)))
      .resize((16,16),Image.Resampling.LANCZOS)).astype(np.int32)
    q=((rgb[:,:,None,:]-pal[None,None,1:,:])**2).sum(3).argmin(2)+1;q[outside_mask(rgb)]=0;cells.append(q.astype('uint8'))
  return encode(join_cells(np.array(cells)))
 def views(self,s,part,data):
  path,index,count=self.images[(s['slug'],'canonical')]
  if path.exists():return sheet_views(path,index,part,count)
  self.missing.append(str(path));assert self.args.allow_incomplete,path
  neutral=np.array(s['palette_rgb'],dtype='uint8');return [neutral[x]for x in split_cells(decode(data))[:8]]
 def raw(self,ptr,size):
  offset=(ptr<<8)-0xc00000;return self.orig[offset:offset+size]
 def mapped(self,ptr):return self.native_map.get(ptr,ptr)
 def part(self,label,data):return self.alloc(label,data)>>8
 def arms(self):
  self.arms_map={}
  # Native arm geometry, with material indices from previously generated gear.
  ca0=self.raw(0xf5c8,0x4000);cc0=self.raw(0xf608,0x8000);hands=self.raw(0xee88,0x4000)
  elbow=decode(self.base[0x320800:0x324800]);elbow[np.isin(elbow,[13,14])]=1
  self.arms_map['elbow']=self.part('shared-black-elbow-pads',encode(elbow))
  for color in ['primary','accent']:
   colored=decode(self.base[0x320800:0x324800]);colored[np.isin(colored,[13,14])]=11 if color=='primary'else 8
   self.arms_map['elbow_'+color]=self.part('shared-'+color+'-elbow-pads',encode(colored))
  sleeve=decode(self.base[0x308800:0x30c800]);sleeve[sleeve==8]=10;sleeve[sleeve==9]=11;sleeve[sleeve==15]=12
  self.arms_map['sleeve']=self.part('shared-short-sleeves',encode(sleeve))
  full=decode(ca0);full[np.isin(full,[2,3,4,7])]=np.array([10 if v==2 else 11 if v==3 else 12 for v in full[np.isin(full,[2,3,4,7])]],dtype='uint8')
  self.arms_map['long']=self.part('shared-long-upper-sleeves',encode(full))
  tattoo=decode(self.base[0x358800:0x35c800]);tattoo[np.isin(tattoo,[8,9,10,11,12,13,14])]=1
  self.arms_map['tattoo']=self.part('shared-upper-arm-ink',encode(tattoo))
  for kind,offset in [('white',0x33c800),('black',0x2fc800)]:
   data=bytearray(cc0);patch=decode(self.base[offset:offset+0x4000])
   if kind=='white':patch[np.isin(patch,[8,9,15])]=15
   else:patch[np.isin(patch,[13,14])]=1
   data[:0x4000]=encode(patch);self.arms_map[kind]=self.part('shared-'+kind+'-wrist-wraps',bytes(data))
  full=decode(cc0);mask=np.isin(full,[2,3,4,7]);full[mask]=np.array([10 if v==2 else 11 if v==3 else 12 for v in full[mask]],dtype='uint8')
  self.arms_map['long_forearms']=self.part('shared-long-forearm-sleeves',encode(full))
  gloves=decode(hands);gloves[gloves!=0]=1;self.arms_map['gloves']=self.part('shared-closed-black-gloves',encode(gloves))
  gloves=decode(hands);mask=np.isin(gloves,[2,3,4,7]);gloves[mask]=np.array([10 if v==2 else 11 if v==3 else 12 for v in gloves[mask]],dtype='uint8')
  self.arms_map['primary_gloves']=self.part('shared-primary-gloves',encode(gloves))
 def compile_character(self,s):
  rank=s['priority'];off=s['profile_offset'];slots,pal,bootpal=self.actor_palette(s)
  resource=0x200+(s['head_model']-128);heads=self.heads(s,pal);source=self.alloc(s['slug']+'-head48',heads,head=True)
  self.descriptor(resource,source,len(heads));self.word(0x1e800+s['head_model']*2,resource|0x8000)
  (self.art/(s['slug']+'-heads.bin')).write_bytes(heads)
  self.r[off+2]=s['head_model']
  if s['target_name']=='Kurrgan':self.r[off+4]=0x83;self.r[off+5]=0x23
  chest=self.r[off+5]&15;abs_size=self.r[off+5]>>4;large=bool(self.r[off+4]&128)
  kind=s['kind'];outfit=0 if kind in['trunks','tights','shorts','jeans']else 1 if kind in['singlet','vest']else 2
  pants=0 if s['leg_mode']==0 else 3 if kind in['singlet','suit','shirt','vest','uniform']else 1
  mode=s['leg_mode'];pads=1 if mode in[0,2] or 'knee' in s['outfit_description']else 0
  self.put(off+286,bytes([outfit|(pants<<4),mode|(pads<<4),0])*4)
  for c in range(4):self.put(0x5d07e+s['face_id']*32+c*8,bytes(slots))
  torso=struct.unpack_from('<H',self.orig,0x1ab9a+2*(chest*4+outfit))[0]
  hips=struct.unpack_from('<H',self.orig,0x1abba+2*(abs_size*4+pants))[0]
  thigh=struct.unpack_from('<H',self.orig,0x1abda+2*((8 if large else 0)+mode))[0]
  lower=struct.unpack_from('<H',self.orig,0x1abfa+2*(pads*8))[0]
  bare=outfit==0;ink=s['target_name']in INK_TORSOS
  raw=self.raw(torso,0x4000)
  covered=kind in ['shirt','suit']
  if not bare or ink:torso_ptr=self.part(s['slug']+'-chest',compile_part(raw,self.views(s,0,raw),pal,bare=bare,ink=ink,covered=covered))
  else:torso_ptr=self.mapped(torso)
  raw=self.raw(hips,0x4000)
  hips_ptr=self.mapped(hips)if s['target_name']in PLAIN_HIPS else self.part(s['slug']+'-abdomen',compile_part(raw,self.views(s,1,raw),pal,preserve_skin=bare,covered=covered))
  raw=self.raw(thigh,0x6c00)
  thigh_ptr=self.mapped(thigh)if mode==0 or s['target_name']in PLAIN_LEGS else self.part(s['slug']+'-upper-legs',compile_part(raw,self.views(s,2,raw),pal,preserve_skin=mode==2))
  raw=self.raw(lower,0x6c00)
  lower_ptr=self.mapped(lower)if s['target_name']not in CUSTOM_BOOTS else self.part(s['slug']+'-knees-boots',compile_part(raw,self.views(s,3,raw),bootpal))
  desc=s['outfit_description'];ca=0xf5c8;cc=0xf608;hand=0xee88
  if 'long-sleeved'in desc:ca=self.arms_map['long'];cc=self.arms_map['long_forearms']
  elif 'arm sleeves'in desc:ca=self.arms_map['long'];cc=self.arms_map['long_forearms']
  elif 'short-sleeved'in desc:ca=self.arms_map['sleeve']
  elif 'tattoo'in desc:ca=self.arms_map['tattoo']
  elif 'elbow pads'in desc:ca=self.arms_map['elbow']
  if s['target_name']=='Funaki':ca=self.arms_map['elbow_primary']
  elif s['target_name']=='Kurt Angle':ca=self.arms_map['elbow_accent']
  if 'white wrist'in desc:cc=self.arms_map['white']
  elif 'black wrist'in desc:cc=self.arms_map['black']
  if 'black gloves'in desc or s['target_name']in['Kane','Rob Van Dam']:hand=self.arms_map['gloves']
  elif s['target_name']=='Goldust':hand=self.arms_map['primary_gloves']
  parts=[torso_ptr,hips_ptr,ca,cc,thigh_ptr,lower_ptr,0xff38,hand]
  self.put(0x1ec00+(s['head_model']-128)*16,struct.pack('<8H',*parts))
  # A matching portrait is derived from the new front head, with no new face.
  arr=decode(heads)[:16,:16];portrait=np.repeat(np.repeat(arr,2,axis=0),2,axis=1)
  # Native portrait entries have14 opaque colors; merge fixed white into the
  # nearest opaque shade and reserve index0 as transparent.
  portrait[portrait==15]=int(((pal[:15]-(232,232,232))**2).sum(1).argmin())
  from ring_tiles import write_tile
  data=bytearray(512)
  for y in range(4):
   for x in range(4):write_tile(data,y*4+x,portrait[y*8:y*8+8,x*8:x*8+8])
  self.put(0x70000+s['face_id']*512,data)
  self.put(0xf3d44+s['face_id']*28,struct.pack('<14H',*(rgb555(c)for c in pal[1:15])))
  s.update({'palette_selectors':slots,'head_source':source,'head_resource':resource,'parts':parts,'body_id':s['head_model'],
   'body_model':s['head_model'],'status':'reference_appearance_v1',
   'appearance_note':'Reference heads and costumes on native modular animation geometry; fine motifs approximate.'})
  if s['target_name']=='Kurrgan':
   s.update({'archetype':'giant','attack':self.kurrgan_report['attack'],'defense':self.kurrgan_report['defense'],
    'skills':self.kurrgan_report['skills'],'moves':self.kurrgan_report['moves'],'finisher':self.kurrgan_report['finisher']})
  print('compiled',s['target_name'],hex(self.pos),flush=True)
 def kurrgan(self):
  s=next(x for x in self.new if x['target_name']=='Kurrgan');off=s['profile_offset'];power=self.rows[10]['profile_offset']
  self.put(off+6,self.base[power+6:power+280]);self.r[off+8]=2|(1<<4);self.put(off+147,bytes([85,95]));self.put(off+149,bytes([85,95]));self.put(off+187,bytes([10,20,50,50]))
  attacks=[4,3,5,2,2,1,4,5,1,4];defense=[5,4,5,2,3,2,5,5,2,4,5,5]
  for at,values in [(13,attacks),(18,defense)]:self.put(off+at,bytes((values[i]+1)|((values[i+1]+1)<<4)for i in range(0,len(values),2)))
  moves=list(struct.unpack_from('<57H',self.r,off+25));moves[3]=198;moves[23]=0x2c8;moves[27]=869;moves[28]=869;moves[29]=961;moves[31]=885;moves[40]=1153;moves[51]=885
  struct.pack_into('<57H',self.r,off+25,*moves);self.r[off+139]=32
  for res,t in zip(struct.unpack_from('<3H',self.r,off+280),['KURRGAN','','KURRGN']):self.name(res,text_bytes(t))
  self.kurrgan_report={'name':'Kurrgan','replaces':'The Hurricane','style':'slow powerful giant','attack':attacks,'defense':defense,
   'skills':{'speed':2,'climb':1,'style':'ORTHODOX','counter':'POWER'},'moves':moves,
   'finisher':{'name':'Paralyzer','slot':31,'native_move':885,'representation':'Cobra Claw, closest standing claw animation'},
   'ground_claw':{'slot':40,'native_move':1153,'name':'Iron Claw'},'aerial_slots_13_14':[moves[13],moves[14]]}
 def menu(self):
  active=[dict(row)for row in self.rows if row['priority']not in self.restored and row['priority']!=67]
  active.append(dict(next(x for x in self.rows if x['priority']==67)));active[-1]['target_name']='Kurrgan'
  old=[dict(row)for row in self.rows if row['priority']in self.restored]
  for row in old:row['former_wwf_name']=row['target_name'];row['target_name']=row['source_name'];row['restored_original']=True
  ordered=active+old;counts=[16,16,16,16,8,12];names=['WWF 01','WWF 02','WWF 03','WWF 04','WWF 05','ORIGINAL']
  ptr=0x48481+8*298;order=ptr+192;cursor=0
  for group,count in enumerate(counts):
   self.word(0x481eb+group*2,ptr);self.word(0x482d9+group*2,order)
   for slot in range(16):
    row=ordered[cursor+slot%count];self.word(ptr,row['profile_offset']&65535);ptr+=2
    self.word(order,(group<<8)|(slot%count));order+=2
   for base in[0x481cd,0x481dc]:self.r[base+group]=count
   resource=struct.unpack_from('<H',self.orig,0x48180+group*2)[0];self.name(resource,text_bytes(names[group]))
   for slot in range(count):
    row=ordered[cursor+slot];row.update({'selection_rank':cursor+slot+1,'page':group,'slot':slot,'encoded_id':(group<<8)|slot,'body_id':self.r[row['profile_offset']+2]})
   cursor+=count
  self.ordered=ordered;self.counts=counts
 def dispatch(self):
  # Call accepted helpers first. Override only models128..194 with eight
  # pointers from the new per-model table; D4 head RAM remains per player.
  stub=bytearray(bytes.fromhex('22 00 e7 c1 08 5a 8b f4 00 81 ab ab a4 be b9 00 00 c9 80 00'))
  branches=[]
  def branch(op):stub.append(op);branches.append(len(stub));stub.append(0)
  branch(0x90);stub.extend(bytes.fromhex('c9 c3 00'));branch(0xb0)
  stub.extend(bytes.fromhex('38 e9 80 00 0a 0a 0a 0a a8'))
  for i,field in enumerate([0xc6,0xc8,0xca,0xcc,0xce,0xd0,0xd2,0xd6]):stub.extend(bytes([0xb9, i*2,0xec,0x95,field]))
  done=len(stub);stub.extend(bytes.fromhex('ab 7a 28 a9 88 ee 6b'))
  for at in branches:stub[at]=(done-at-1)&255
  assert len(stub)<0x100;self.put(0x1ea00,stub);self.put(0x10bef,bytes.fromhex('22 00 ea c1 60 ea'))
 def repack_names(self):
  # Stay inside the proven native C8 positive-offset name pool. All selected
  # WWF words come from the accepted base; restored names use original words.
  for index in range(104):
   for res in struct.unpack_from('<3H',self.orig,0x48481+index*298+280):
    if res not in self.name_data:self.name_data[res]=original_text(self.base,res)
  pool=0x3ff800;seen={}
  for res,data in self.name_data.items():
   if data in seen:ptr=seen[data]
   else:
    if pool>=0x3ff800 and pool+len(data)>0x400000:pool=0x82a65
    assert pool+len(data)<=0x834e1 if pool<0x3ff800 else pool+len(data)<=0x400000
    ptr=pool;self.put(ptr,data);pool+=len(data);seen[data]=ptr
   self.put(0x80000+res,(ptr-0x80000).to_bytes(3,'little'))
 def finish(self):
  self.repack_names()
  for (cat,slot),data in self.saved_locked.items():
   start,step,_=PALETTES[cat];assert self.r[start+slot*step:start+(slot+1)*step]==data
  for row in self.rows:
   off=row['profile_offset']
   if row['priority']<=5:assert self.r[off:off+298]==self.base[off:off+298]
   if row['priority']in self.restored:assert self.r[off:off+298]==self.orig[off:off+298]
  self.r[0xffd5]=0x35;self.r[0xffd7]=0x0d
  self.put(0x400000,self.r[:0x10000])
  for h in[0xffc0,0x40ffc0]:self.put(h+0x1c,bytes.fromhex('ff ff 00 00'))
  check=sum(self.r)&65535
  for h in[0xffc0,0x40ffc0]:self.put(h+0x1c,struct.pack('<HH',check^65535,check))
  assert sum(self.r)&65535==check and len(self.r)==0x800000
  missing=sorted(set(self.missing));name=NAME+'-development'if missing else NAME
  (self.out/(name+'.sfc')).write_bytes(self.r)
  report={'version':name,'rom_sha256':digest(self.r),'base_sha256':BASE_SHA,'rom_bytes':len(self.r),'mapping':'8MiB ExHiROM',
   'page_counts':self.counts,'wwf_count':72,'restored_original_count':12,'reference_revisions':67,'accepted_first_five_preserved':True,
   'missing_development_art':missing,'rows':self.ordered,'appearances':self.new,'kurrgan':self.kurrgan_report,'allocations':self.allocations,
   'last_expansion_offset':hex(self.pos),'remaining_addressable_bytes':0x7e0000-self.pos,
   'limitations':['Costumes use canonical reference views retargeted onto native modular poses; fine motifs are approximations.',
   'Some plain body/leg parts and gear are native modules in matching colors.','Existing movesets retained except Kurrgan and restored native profiles.']}
  (self.out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  fields=['selection_rank','target_name','source_name','page','slot','body_id','restored_original'];buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=fields,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(self.ordered);(self.out/'roster.csv').write_text(buf.getvalue())
  print('BUILD',name,'SHA256',digest(self.r),'free',hex(0x7e0000-self.pos),'missing',len(missing),flush=True)
 def run(self):
  self.restore();self.native_parts();self.palette_slots();self.arms();self.kurrgan()
  for s in self.new:self.compile_character(s)
  self.menu();self.dispatch();self.finish()

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-rom',type=Path,default=ROOT/'build/mankind-tie-v2/raw-attitude-reference-five-v2-mankind-tie.sfc');p.add_argument('--output-dir',type=Path,default=ROOT/'build/full-roster-v1');p.add_argument('--allow-incomplete',action='store_true');Builder(p.parse_args()).run()
