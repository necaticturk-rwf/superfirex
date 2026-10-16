"""Add reference-driven Triple H, Mankind and Ministry Undertaker to the pair ROM.

All patches are ROM changes. Custom geometry retains native animation indexes;
previous Austin/Rock resources, moves, abilities and ring data are preserved.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image
from ring_tiles import tile, write_tile
from build_undertaker import ips

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets/reference-trio-v1'
NAME = 'raw-attitude-reference-five-v1'
BASE_SHA = '8456e9dab3d7e6ad01b38d4dd33b9fe8b399d31fe98a2849c643cd3a930a0eee'
SPECS = {
    'hhh': {'rank': 3, 'model': 26, 'resource': 0x62, 'head_source': 0xf4984,
            'skin': [(136,72,40),(208,136,88),(248,192,144)],
            'hair': [(48,24,12),(104,64,32)],
            'line': [(192,192,192),(240,240,232)],
            'tights': [(144,144,144),(200,200,200),(232,232,232)],
            'pants': [(16,16,24),(48,48,56)],
            'slots': [29,71,77,79,0,0,1,2], 'body': 0x82, 'sizes': 0x12,
            'gear': '001000', 'parts': {0xc6:0xf760,0xc8:0xf308,0xca:0xf208,0xcc:0xf488,0xd0:0xf838}},
    'mankind': {'rank': 5, 'model': 28, 'resource': 0x63, 'head_source': 0xf6184,
            'skin': [(120,64,40),(192,128,88),(232,184,144)],
            'hair': [(32,16,8),(104,56,24)],
            'line': [(168,168,168),(216,216,208)],
            'tights': [(32,16,16),(56,32,24),(88,56,40)],
            'pants': [(40,24,24),(72,40,32)],
            'slots': [25,70,76,77,95,0,1,0], 'body': 0x81, 'sizes': 0x32,
            'gear': '320100', 'parts': {0xc6:0xef08,0xca:0xf088,0xcc:0xf3c8}},
    'undertaker': {'rank': 4, 'model': 56, 'resource': 0x61, 'head_source': 0x1e7e0,
            'skin': [(112,96,80),(184,168,144),(224,216,192)],
            'hair': [(8,8,8),(32,24,24)],
            'line': [(64,64,64),(112,112,104)],
            'tights': [(8,8,8),(24,24,32),(48,48,56)],
            'pants': [(16,16,24),(48,48,56)],
            'slots': [28,72,73,78,0,0,1,0], 'body': 3, 'sizes': 0x12,
            'gear': '320100', 'parts': {0xc6:0xf448,0xca:0xf588,0xcc:0xf7cc,0xd6:0xf8a4}},
}

def sha(data): return hashlib.sha256(data).hexdigest()
def rgb555(rgb): return sum(((int(v)*31+127)//255)<<shift for v,shift in zip(rgb,[0,5,10]))
def palette(label):
    s=SPECS[label]
    return np.array([(0,0,0),(49,41,16),*s['skin'],*s['hair'],s['skin'][-1],
                     *s['line'],*s['tights'],*s['pants'],(232,232,232)],dtype=np.int32)
def decode(data):
    return np.block([[tile(data,y*16+x) for x in range(16)] for y in range(len(data)//512)])
def encode(indices):
    data=bytearray(indices.size//2)
    for y in range(indices.shape[0]//8):
        for x in range(16): write_tile(data,y*16+x,indices[y*8:y*8+8,x*8:x*8+8])
    return bytes(data)
def cells(path,rows):
    im=Image.open(path).convert('RGB')
    for row in range(rows):
        for col in range(8):
            yield np.asarray(im.crop((round(col*im.width/8),round(row*im.height/rows),
                round((col+1)*im.width/8),round((row+1)*im.height/rows)))
                .resize((16,16),Image.Resampling.LANCZOS)).astype(np.int32)
def outside_mask(rgb):
    dark=rgb.max(axis=2)<15;outside=np.zeros((16,16),bool);queue=deque()
    for y in range(16):
        for x in range(16):
            if (x in [0,15] or y in [0,15]) and dark[y,x]:
                outside[y,x]=True;queue.append((y,x))
    while queue:
        y,x=queue.popleft()
        for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
            yy,xx=y+dy,x+dx
            if 0<=yy<16 and 0<=xx<16 and dark[yy,xx] and not outside[yy,xx]:
                outside[yy,xx]=True;queue.append((yy,xx))
    return outside

def build(args):
    base=args.base_rom.read_bytes();assert sha(base)==BASE_SHA
    r=bytearray(base);rows=json.loads((ROOT/'build/attitude-native-beta/manifest.json').read_text())['rows']
    artdir=args.output_dir/'art';artdir.mkdir(parents=True,exist_ok=True)
    def put(addr,data):r[addr:addr+len(data)]=data
    def preview(label,indices,owner):
        Image.fromarray(palette(owner)[indices].astype('uint8')).resize(
            (512,indices.shape[0]*4),Image.Resampling.NEAREST).save(artdir/(label+'.png'))
    def nearest(rgb,label,allowed):
        colors=palette(label)[allowed]
        return np.array(allowed,dtype=np.uint8)[((rgb[:,:,None,:]-colors[None,None,:,:])**2).sum(axis=3).argmin(axis=2)]
    used_models={base[row['profile_offset']+2] for row in rows}
    used_resources={struct.unpack_from('<H',base,0x1b15e+model*2)[0]&0x7fff for model in used_models}
    assert not used_resources.intersection({0x61,0x62,0x63,0x64})
    assert not used_models.intersection({26,28,56})
    assert set(base[0x1e800:0x20000])=={255}
    # Four unused compressed head streams are replaced by two raw streams.
    # Redirect the remaining displaced stream to the untouched neutral head.
    put(0x15b3b8+0x64*8,base[0x15b3b8+0x39*8:0x15b3b8+0x39*8+8])
    report={}
    for label,spec in SPECS.items():
        original=decode((ASSETS/(label+'-heads-baseline.bin')).read_bytes());out=original.copy()
        for i,rgb in enumerate(cells(ASSETS/(label+'-heads-generated.png'),6)):
            q=nearest(rgb,label,list(range(1,8)));q[outside_mask(rgb)]=0
            out[i//8*16:i//8*16+16,i%8*16:i%8*16+16]=q
        data=encode(out);assert len(data)==0x1800
        put(spec['head_source'],data)
        descriptor=(0xc00000+spec['head_source']).to_bytes(3,'little')+struct.pack('<H',len(data))+bytes([0,0,0x81])
        put(0x15b3b8+spec['resource']*8,descriptor)
        (artdir/(label+'-heads.bin')).write_bytes(data);preview(label+'-heads',out,label)
        report[label]={'rank':spec['rank'],'head_model':spec['model'],'head_resource':hex(spec['resource']),
            'head_source':hex(spec['head_source']),'head_views':48,'changed_head_pixels':int(np.count_nonzero(out!=original)),
            'part_overrides':{hex(k):hex(v) for k,v in spec['parts'].items()}}
    # Palette slots were previously unused by every native face/costume.
    category_layout=[(0x5dffe,6),(0x5e0d0,4),(0x5e1fc,4),(0x5e33c,6),(0x5e522,4),
                     (0x5e6a2,4),(0x5e792,6),(0x5e9c0,4)]
    for label,spec in SPECS.items():
        categories=[(0,spec['skin']),(1,spec['hair']),(2,spec['line']),(3,spec['tights'])]
        if label=='mankind':categories.append((4,spec['pants']))
        if label=='hhh':categories.append((7,[(192,192,192),(240,240,232)]))
        for cat,values in categories:
            slot=spec['slots'][cat]
            assert all(base[0x5d07e+face*32+c*8+cat]!=slot for face in range(104)for c in range(4)),(label,cat,slot)
            addr,step=category_layout[cat];put(addr+slot*step,struct.pack('<'+'H'*len(values),*(rgb555(v)for v in values)))
        row=rows[spec['rank']-1];off=row['profile_offset']
        r[off+2]=spec['model'];r[off+4]=spec['body'];r[off+5]=spec['sizes'];put(off+286,bytes.fromhex(spec['gear'])*4)
        for costume in range(4):put(0x5d07e+row['face_id']*32+costume*8,bytes(spec['slots']))
    # Guard each reclaimed storage interval against all current native gear
    # combinations, plus the Austin/Rock custom pointers from the base patch.
    active={0xefc8,0xf208,0xf308,0xf408,0xf5c8,0xf608,0xee88}
    for data in [base,r]:
        for row in rows:
            off=row['profile_offset'];chest=data[off+5]&15;abs_size=data[off+5]>>4
            for c in range(4):
                g=data[off+286+c*3:off+289+c*3]
                for table,index in [(0x1ab9a,chest*4+(g[0]&15)),(0x1abba,abs_size*4+(g[0]>>4)),
                    (0x1abda,(8 if data[off+4]&128 else 0)+(g[1]&15)),(0x1abfa,(g[1]>>4)*8+(g[2]&15)),(0x1ac1a,g[2]>>4)]:
                    active.add(struct.unpack_from('<H',data,table+index*2)[0])
    jobs=[('mankind-torso','undertaker-torso',0xef08,'mankind',[1,2,3,4,5,6,8,9,15]),
          ('undertaker-torso','undertaker-torso',0xf448,'undertaker',list(range(1,16))),
          ('hhh-torso','torso',0xf760,'hhh',list(range(1,8))),
          ('mankind-upperarms','upperarms',0xf088,'mankind',[1,2,3,4,5,6,8,9,15]),
          ('undertaker-upperarms','upperarms',0xf588,'undertaker',list(range(1,16))),
          ('undertaker-forearms','forearms',0xf7cc,'undertaker',list(range(1,16))),
          ('undertaker-hands','hands',0xf8a4,'undertaker',list(range(1,16)))]
    for label,baseline,ptr,owner,allowed in jobs:
        assert ptr not in active,(label,'reclaimed part used by native costume')
        original=decode((ASSETS/(baseline+'-baseline.bin')).read_bytes());out=original.copy()
        source=ASSETS/(label+'-generated.png')
        for i,rgb in enumerate(cells(source,16)):
            y,x=i//8*16,i%8*16;orig=original[y:y+16,x:x+16];mask=orig!=0
            if not label.endswith('-hands') and np.count_nonzero(np.isin(orig,[2,3,4,7]))<5 and np.count_nonzero(mask)<12:continue
            if label=='hhh-torso':
                # The generated back motif is a cosmetic mask. Retain native
                # chest shading and never transfer that motif onto front poses.
                # The first five native rows share the five facing directions.
                if i//8<5 and i%8 in [3,4]:
                    source_col=5 if i%8==3 else 6
                    back_rgb=list(cells(source,16))[i//8*8+source_col]
                    ink=(back_rgb.max(axis=2)<110)&(~outside_mask(back_rgb))&np.isin(orig,[2,3,4,7])
                    out[y:y+16,x:x+16][ink]=np.where(back_rgb[ink].mean(axis=1)>45,6,5)
                continue
            quantized=nearest(rgb,owner,allowed)
            # Keep empty/marker cells and the native silhouette in all frames.
            patch=out[y:y+16,x:x+16];patch[mask]=quantized[mask]
        data=encode(out);assert len(data)==0x4000;put((ptr<<8)-0xc00000,data);preview(label,out,owner)
        report[label]={'pointer':hex(ptr),'changed_pixels':int(np.count_nonzero(out!=original))}
    # Reuse the generated Austin wrist-band mask, encoding it in each new
    # character's white trim palette instead of Austin's black trunks shades.
    wrist_source=ROOT/'assets/reference-pair-v1/austin-wrists-generated.png'
    for owner,ptr in [('hhh',0xf488),('mankind',0xf3c8)]:
        assert ptr not in active
        original=decode((ASSETS/'forearms-baseline.bin').read_bytes());out=original.copy()
        for i,rgb in enumerate(cells(wrist_source,16)):
            y,x=i//8*16,i%8*16;orig=original[y:y+16,x:x+16];skin=np.isin(orig,[2,3,4,7])
            if skin.sum()<5:continue
            mask=(rgb.max(axis=2)<95)&(rgb.min(axis=2)<70)&(~outside_mask(rgb))&skin
            out[y:y+16,x:x+16][mask]=np.where(rgb[mask].mean(axis=1)>32,9,8)
        put((ptr<<8)-0xc00000,encode(out));preview(owner+'-wrists',out,owner)
        report[owner+'-wrists']={'pointer':hex(ptr),'changed_pixels':int(np.count_nonzero(out!=original))}
    # Lower-leg nodes use the actor's second palette: black shoe shades and
    # white knee-wrap shades. Keep the native 216-cell animation geometry.
    assert 0xf838 not in active
    original=decode((ASSETS/'hhh-lowerlegs-baseline.bin').read_bytes());out=original.copy()
    legpal=np.array([(0,0,0),(49,41,16),(0,0,0),(112,64,16),(184,72,16),(232,88,32),
        (248,192,112),(248,216,184),(16,16,24),(48,48,56),(16,16,24),(16,16,24),
        (48,48,56),(192,192,192),(240,240,232),(232,232,232)],dtype=np.int32)
    allowed=[1,8,9,10,12,13,14,15]
    for half in ['a','b']:
        for i,rgb in enumerate(cells(ASSETS/('hhh-lowerlegs-'+half+'-generated.png'),16)):
            index=i+(128 if half=='b' else 0)
            if index>=216:break
            y,x=index//8*16,index%8*16;orig=original[y:y+16,x:x+16];mask=orig!=0
            if np.count_nonzero(mask)<8:continue
            colors=legpal[allowed]
            q=np.array(allowed,dtype=np.uint8)[((rgb[:,:,None,:]-colors[None,None,:,:])**2).sum(axis=3).argmin(axis=2)]
            out[y:y+16,x:x+16][mask]=q[mask]
    data=encode(out);assert len(data)==0x6c00;put(0x383800,data)
    Image.fromarray(legpal[out].astype('uint8')).resize((512,1728),Image.Resampling.NEAREST).save(artdir/'hhh-lowerlegs.png')
    report['hhh-lowerlegs']={'pointer':'0xf838','views':216,'changed_pixels':int(np.count_nonzero(out!=original))}
    # Dispatch only the three new models; chain the original pair helper for
    # every other model, preserving Austin/Rock behavior and the return contract.
    stub=bytearray();labels={};branches=[]
    def emit(s):stub.extend(bytes.fromhex(s))
    def branch(op,label):emit(op);branches.append((len(stub),label));stub.append(0)
    def mark(label):labels[label]=len(stub)
    emit('08 5a a9 88 ee 95 d6 a4 be b9 00 00')
    for label,spec in SPECS.items():
        emit('c9');stub.extend(struct.pack('<H',spec['model']));branch('d0','next-'+label)
        for field,ptr in spec['parts'].items():emit('a9');stub.extend(struct.pack('<H',ptr));emit('95');stub.append(field)
        branch('80','done');mark('next-'+label)
    emit('7a 28 22 00 e5 c1 6b');mark('done');emit('7a 28 a9 88 ee 6b')
    for at,label in branches:
        delta=labels[label]-(at+1);assert -128<=delta<=127;stub[at]=delta&255
    assert base[0x10bef:0x10bf5]==bytes.fromhex('22 00 e5 c1 60 ea')
    assert len(stub)<0x200 and set(base[0x1e600:0x1e600+len(stub)])=={255}
    put(0x1e600,stub);put(0x10bef,bytes.fromhex('22 00 e6 c1 60 ea'))
    # Only appearance fields in these three native records can change.
    modified={s['rank'] for s in SPECS.values()}
    for row in rows:
        off=row['profile_offset'];changed=[i for i in range(298)if base[off+i]!=r[off+i]]
        assert not changed or row['priority'] in modified
        assert all(i in [2,4,5] or 286<=i<298 for i in changed)
    put(0xffdc,bytes.fromhex('ffff0000'));checksum=sum(r)&65535;put(0xffdc,struct.pack('<HH',checksum^65535,checksum))
    assert len(r)==len(base) and sum(r)&65535==checksum
    args.output_dir.mkdir(parents=True,exist_ok=True);(args.output_dir/(NAME+'.sfc')).write_bytes(r)
    (args.output_dir/(NAME+'-from-austin-rock-v1.ips')).write_bytes(ips(base,r))
    result={'version':NAME,'base_sha256':BASE_SHA,'rom_sha256':sha(r),'modified_roster_ranks':[3,4,5],
        'retained_reference_ranks':[1,2],'other_81_native_profiles_unchanged':True,'moves_abilities_unchanged':True,
        'new_head_views':144,'art':report,'notes':['Only ranks 1-5 have received individual reference revisions.',
        'Names, portraits, moves and abilities retain previous native-beta values.',
        'Tiny tattoos and clothing emblems are pixel approximations.']}
    (args.output_dir/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-rom',type=Path,default=ROOT/'build/reference-pair-v1/raw-austin-rock-reference-v1.sfc')
    p.add_argument('--output-dir',type=Path,default=ROOT/'build/reference-trio-v1')
    build(p.parse_args())
