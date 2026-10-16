"""Fix Mankind's closed shirt/tie across chest and abdomen, retaining the other looks."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from PIL import Image
from build_reference_trio import cells, decode, encode, palette
from build_undertaker import ips

ROOT=Path(__file__).resolve().parents[1]
NAME='raw-attitude-reference-five-v2-mankind-tie'
BASE_SHA='cf330bb7c4e3ed3966667ee5547e6c75103c2b1baffdf60686d253e41c3f8044'
ASSETS=ROOT/'assets/mankind-tie-v2'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--base-rom',type=Path,default=ROOT/'build/reference-trio-v1/raw-attitude-reference-five-v1.sfc')
p.add_argument('--output-dir',type=Path,default=ROOT/'build/mankind-tie-v2')
a=p.parse_args();base=a.base_rom.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA;r=bytearray(base)
rows=json.loads((ROOT/'build/attitude-native-beta/manifest.json').read_text())['rows']
# F9E8 belongs to an unused large-thigh costume collection, with 0x6c00 bytes
# before the next native collection. Only its first 0x4000 bytes are reclaimed.
for row in rows:
 off=row['profile_offset']
 for c in range(4):
  g=base[off+286+c*3:off+289+c*3]
  idx=(8 if base[off+4]&128 else 0)+(g[1]&15)
  assert struct.unpack_from('<H',base,0x1abda+idx*2)[0]!=0xf9e8
assert set(base[0x1e700:0x1e730])=={255}
assert base[0x10bef:0x10bf5]==bytes.fromhex('22 00 e6 c1 60 ea')
a.output_dir.mkdir(parents=True,exist_ok=True);art=a.output_dir/'art';art.mkdir(exist_ok=True)
metrics={}
for label,source,dest,allowed in [('chest',0x2f0800,0x2f0800,[5,8,9,15]),
                                ('hips',0x354800,0x39e800,[5,8,9,13,14,15])]:
 original=decode(base[source:source+0x4000]);out=original.copy();pal=palette('mankind')
 for i,rgb in enumerate(cells(ASSETS/(label+'-generated.png'),16)):
  y,x=i//8*16,i%8*16;orig=original[y:y+16,x:x+16];mask=orig!=0
  if mask.sum()<12:continue
  colors=pal[allowed];q=np.array(allowed,dtype=np.uint8)[((rgb[:,:,None,:]-colors[None,None,:,:])**2).sum(axis=3).argmin(axis=2)]
  out[y:y+16,x:x+16][mask]=q[mask]
 data=encode(out);assert len(data)==0x4000;r[dest:dest+len(data)]=data
 Image.fromarray(pal[out].astype('uint8')).resize((512,1024),Image.Resampling.NEAREST).save(art/('mankind-'+label+'.png'))
 (art/('mankind-'+label+'.bin')).write_bytes(data)
 metrics[label]={'rom_offset':hex(dest),'changed_pixels':int(np.count_nonzero(out!=original))}
# Keep the accepted three-character dispatcher intact. Call it first, then
# redirect ONLY Mankind's abdomen collection. Preserve native helper contract.
stub=bytes.fromhex('22 00 e6 c1 08 5a a4 be b9 00 00 c9 1c 00 d0 05 a9 e8 f9 95 c8 7a 28 a9 88 ee 6b')
r[0x1e700:0x1e700+len(stub)]=stub;r[0x10bef:0x10bf5]=bytes.fromhex('22 00 e7 c1 60 ea')
r[0xffdc:0xffe0]=bytes.fromhex('ff ff 00 00');check=sum(r)&65535;struct.pack_into('<HH',r,0xffdc,check^65535,check)
assert len(r)==len(base) and sum(r)&65535==check
allowed_regions=[(0xffdc,0xffe0),(0x10bef,0x10bf5),(0x1e700,0x1e700+len(stub)),
                 (0x2f0800,0x2f4800),(0x39e800,0x3a2800)]
changed=[i for i,(old,new)in enumerate(zip(base,r))if old!=new]
assert all(any(start<=i<end for start,end in allowed_regions)for i in changed)
for row in rows:
 off=row['profile_offset'];assert r[off:off+298]==base[off:off+298]
# Supply unchanged heads to the existing cold-boot five-character checker.
for label in ['hhh','mankind','undertaker']:
 source=ROOT/'build/reference-trio-v1/art'/(label+'-heads.bin');(art/source.name).write_bytes(source.read_bytes())
manifest=json.loads((ROOT/'build/reference-trio-v1/manifest.json').read_text())
manifest.update({'version':NAME,'base_sha256':BASE_SHA,'rom_sha256':hashlib.sha256(r).hexdigest(),
 'modified_roster_ranks':[5],'changed_bytes':len(changed),'changed_regions':[[hex(s),hex(e)]for s,e in allowed_regions],
 'all_native_profiles_unchanged':True,'all_other_character_graphics_unchanged':True,
 'ring_bytes_unchanged':True,'mankind_shirt_art':metrics})
manifest['art']['mankind']['part_overrides']['0xc8']='0xf9e8'
manifest['notes']=['Only Mankind chest/abdomen art is revised; all other character art stays byte-identical.',
 'The closed white shirt covers the previous brown singlet abdomen; a narrow black tie continues to the waist.',
 'Profiles, heads, palettes, moves, abilities, portraits and ring data remain unchanged.']
(a.output_dir/(NAME+'.sfc')).write_bytes(r);(a.output_dir/(NAME+'-from-reference-five-v1.ips')).write_bytes(ips(base,r))
(a.output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:manifest[k]for k in ['version','rom_sha256','changed_bytes','mankind_shirt_art']},indent=2))
