"""Verify the 12 exact restorations and five accepted appearances, then export game crops."""
from pathlib import Path
import ctypes as C,hashlib,json,struct
from PIL import Image,ImageDraw,ImageFont
from headless_snes import Emulator
ROOT=Path(__file__).resolve().parents[1];d=ROOT/'build/full-roster-v1';out=d/'runtime';r=(d/'raw-attitude-72-reference-v1.sfc').read_bytes();b=(ROOT/'build/mankind-tie-v2/raw-attitude-reference-five-v2-mankind-tie.sfc').read_bytes();o=(ROOT/'Super Fire Pro Wrestling X Premium (Japan) [T-En by Sydra v7].sfc').read_bytes();m=json.loads((d/'manifest.json').read_text());rows=m['rows'];assert hashlib.sha256(r).hexdigest()==m['rom_sha256'];assert len(r)==0x800000
for head in [0xffc0,0x40ffc0]:
 assert r[head+21]==0x35 and r[head+23]==13;inv,check=struct.unpack_from('<HH',r,head+28);assert inv^check==65535 and sum(r)&65535==check
restored=[]
for row in rows:
 off=row['profile_offset'];face=r[off]
 if row.get('restored_original'):
  assert r[off:off+298]==o[off:off+298]
  for at,n in [(0x70000+face*512,512),(0xf3d44+face*28,28),(0x5d07e+face*32,32)]:assert r[at:at+n]==o[at:at+n]
  restored.append(row['target_name'])
 elif row['selection_rank']<=5:
  assert r[off:off+298]==b[off:off+298]
  for at,n in [(0x70000+face*512,512),(0xf3d44+face*28,28),(0x5d07e+face*32,32)]:assert r[at:at+n]==b[at:at+n]
 elif row['target_name']!='Kurrgan':assert r[off+6:off+280]==b[off+6:off+280],row['target_name']
assert len(restored)==12 and len(rows)==84 and all(x.get('restored_original')for x in rows[72:]);assert rows[71]['target_name']=='Kurrgan'
for table,count,size in [(0x1ab9a,16,0x4000),(0x1abba,16,0x4000),(0x1abda,16,0x6c00),(0x1abfa,16,0x6c00),(0x1ac1a,4,0x4000)]:
 for i in range(count):
  old=struct.unpack_from('<H',o,table+i*2)[0]*256-0xc00000;ptr=struct.unpack_from('<H',r,table+i*2)[0];new=ptr*256-(0xc00000 if ptr>=0xc000 else 0);assert r[new:new+size]==o[old:old+size],('native original part',hex(table),i)
assert not any(x['target_name']in ['The Hurricane','Vince McMahon','Shane McMahon','Chyna','Lita','Trish Stratus','Sable','Stephanie McMahon','Tori','Jacqueline','Ivory','Molly Holly','Luna Vachon']for x in rows[:72])
e=Emulator(d/'raw-attitude-72-reference-v1.sfc','/tmp/sfpx-snes9x-1.62.3/libretro/snes9x_libretro.so')
def memory():return C.string_at(e.core.retro_get_memory_data(2),131072)
def word(ram,at):return struct.unpack_from('<H',ram,at)[0]
for pair in range(3):
 e.load(out/f'match-{pair:02}.state');e.run(1);ram=memory()
 for port in range(2):
  if pair*2+port>=5:continue
  for field,size in [(0xc6,0x4000),(0xc8,0x4000),(0xca,0x4000),(0xcc,0x4000),(0xce,0x6c00),(0xd0,0x6c00),(0xd2,0x4000),(0xd6,0x4000)]:
   ptr=word(ram,0xa79+port*0x104+field);assert ptr>=0xc000;at=ptr*256-0xc00000;assert r[at:at+size]==b[at:at+size]
selected=[0,1,2,3,4,5,6,7,8,9,10,12,13,16,17,18,30,71];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13);canvas=Image.new('RGB',(6*176,3*318),(20,23,28));draw=ImageDraw.Draw(canvas)
for tile,index in enumerate(selected):
 e.load(out/f'match-{index//2:02}.state');e.run(1);ram=memory();port=index%2;base=0xa79+port*0x104;x=word(ram,base)-word(ram,0xfa3);y=word(ram,base+4)-word(ram,0xfa5)
 crop=e.frame().crop((x-22,y-70,x+22,y+2)).resize((176,288),Image.Resampling.NEAREST);tx=tile%6*176;ty=tile//6*318;canvas.paste(crop,(tx,ty));draw.text((tx+4,ty+292),rows[index]['target_name'][:23],fill='white',font=font)
canvas.save(out/'roster-showcase.png');report={'rom_sha256':m['rom_sha256'],'rom_size':len(r),'exhirom_headers_and_checksum_valid':True,'accepted_five_profiles_portraits_palettes_and_runtime_part_bytes_preserved':True,'restored_profiles_portraits_and_all_four_costume_selectors_byte_exact':restored,'other_wwf_moves_and_abilities_preserved':True,'roster_order_72_wwf_then_12_original':True,'kurrgan_replaces_hurricane_at_wwf_rank_72':True};(out/'static-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS static and accepted-five appearance preservation')
