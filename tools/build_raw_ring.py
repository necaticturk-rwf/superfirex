from pathlib import Path
import argparse,hashlib,struct
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Build the RAW IS WAR ring v3 ROM and IPS patch for Sydra v7.')
parser.add_argument('--rom',type=Path,required=True)
parser.add_argument('--output',type=Path,default=root/'build/raw-is-war-v3.sfc')
args=parser.parse_args()
original=args.rom.read_bytes()
expected='30a774f32e3e132d7e0c16f964a59b8720c1cc081e20159f85a22635f13e28fa'
if hashlib.sha256(original).hexdigest()!=expected:
    parser.error('Unsupported input ROM. Requires the exact unheadered Sydra v7 ROM documented in research/RAW_RING.md.')
rom=bytearray(original)
baseline=(root/'assets/raw-ring/hwa-baseline.bin').read_bytes()
if hashlib.sha256(baseline).hexdigest()!='02c10ffd74bdf3e7754bcefaf331dc9c32c108d8cd30b32142004a6a90392789':
    parser.error('Baseline graphics asset checksum mismatch.')
# Allocate palette 4 to the apron; the center logo no longer needs it.
def color(palette,index,rgb):
 r,g,b=rgb;value=(r//8)|((g//8)<<5)|((b//8)<<10);struct.pack_into('<H',rom,palette+index*2,value)
p4=[(0,0,0),(208,8,16),(112,0,8),(240,240,240),(0,0,0),(56,56,56),(32,32,32),(8,8,8),(40,40,40),(24,24,24),(8,8,8),(24,24,24),(24,24,24),(64,64,64),(32,32,32),(8,8,8)]
for i,rgb in enumerate(p4):color(0x1e07d,i,rgb)
for p in (0x1e09d,0x1e0bd):
 for i,rgb in {1:(224,224,224),2:(176,184,192),3:(200,208,216),4:(192,16,24),5:(96,0,8),6:(192,16,24),7:(96,0,8),8:(192,16,24),9:(96,0,8),10:(64,64,64),11:(32,32,32),12:(16,16,16),13:(40,40,40),14:(16,16,16)}.items():color(p,i,rgb)
# Neutralize the shared blue stairs and platform palette.
for i,rgb in {1:(64,64,64),2:(40,40,40),3:(24,24,24),4:(16,16,16),11:(48,48,48),12:(24,24,24),13:(64,64,64)}.items():color(0x1e0dd,i,rgb)
from ring_tiles import build_geometry
bg2=(root/'assets/raw-ring/hwa-bg2-baseline.bin').read_bytes()
if hashlib.sha256(bg2).hexdigest()!='64596a384cd0ca6cc3ea06598ff61061a67612bed833df1e2dd86f273bbf1b3d':
    parser.error('BG2 baseline graphics checksum mismatch.')
build_geometry(rom,original,baseline,bg2,root/'assets/raw-ring/raw-is-war-banner.png')
# HWF loads a separate set of ring palettes. RANDOM can select either ring.
# Keep each ring's spectator palettes (0-3) intact; unify only ring palettes 4-7.
rom[0x1e17d:0x1e1fd]=rom[0x1e07d:0x1e0fd]
# RANDOM synthesizes colors in RAM instead of loading either fixed palette.
# At the game's full-CGRAM DMA wrapper, normalize only ring palettes 4-7.
# Gate on the DMA source/size/destination and the match background palette.
# Menus, sprite palettes, SRAM, and the caller's registers remain intact.
hook_offset=0x15fa20
hook=bytearray();labels={};branches=[]
def emit(hexbytes):hook.extend(bytes.fromhex(hexbytes))
def branch(op,label):
 emit(op);branches.append((len(hook),label));hook.append(0)
def mark(label):labels[label]=len(hook)
emit('08 c2 30 48 da 5a')  # PHP; REP #$30; PHA; PHX; PHY
for address,value in [(0x004300,0x2200),(0x004302,0x059e),(0x004305,0x0200),(0x0005a0,0x2528),(0x0005a2,0x2549)]:
 emit('af');hook.extend(address.to_bytes(3,'little'))
 emit('c9');hook.extend(value.to_bytes(2,'little'));branch('d0','restore')
emit('a2 7e 00');mark('copy')
emit('bf 7d e0 c1 9f 1e 06 00 ca ca');branch('10','copy')
mark('restore');emit('7a fa 68 28 a9 01 8d 0b 42 6b')
for at,label in branches:
 delta=labels[label]-(at+1);assert -128<=delta<=127;hook[at]=delta&255
assert original[0xd63c:0xd641]==bytes.fromhex('a9 01 8d 0b 42')
assert all(x==255 for x in original[hook_offset:hook_offset+len(hook)])
rom[hook_offset:hook_offset+len(hook)]=hook
rom[0xd63c:0xd641]=bytes.fromhex('22 20 fa d5 ea')
# Match setup reads four resource IDs from the selected/random arena descriptor.
# Replace only those four loads with HWA IDs; retain the original destinations,
# animation code, table layout, and all other uses of the generic resource loader.
for offset,expected_bytes,resource in [(0x5c203,'b9 ce af',0xe2),
                                     (0x5c20f,'b9 d0 af',0xb1),
                                     (0x5c21b,'b9 d2 af',0xc1),
                                     (0x5c226,'b9 d4 af',0xa2)]:
    assert original[offset:offset+3]==bytes.fromhex(expected_bytes)
    rom[offset:offset+3]=b'\xa9'+(0x4000|resource).to_bytes(2,'little')
rom[0xffdc:0xffe0]=bytes.fromhex('ffff0000');checksum=sum(rom)&65535;struct.pack_into('<HH',rom,0xffdc,checksum^65535,checksum)
if args.output.resolve()==args.rom.resolve():
    parser.error('Output must not overwrite the input ROM.')
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_bytes(rom)
# Standard IPS patch, including the SNES checksum update. No original ROM is distributed.
patch=bytearray(b'PATCH');i=0
while i<len(original):
    if original[i]==rom[i]:i+=1;continue
    start=i;i+=1
    while i<len(original) and i-start<65535:
        if original[i]!=rom[i]:i+=1;continue
        next_change=i
        while next_change<min(i+8,len(original)) and original[next_change]==rom[next_change]:next_change+=1
        if next_change<min(i+8,len(original)) and next_change-start<65535:i=next_change+1
        else:break
    data=rom[start:i]
    patch+=start.to_bytes(3,'big')+len(data).to_bytes(2,'big')+data
patch+=b'EOF'
patch_path=root/'patches/raw-is-war-v3.ips';patch_path.parent.mkdir(parents=True,exist_ok=True);patch_path.write_bytes(patch)
# Independently apply the serialized IPS records and compare the complete output.
applied=bytearray(original);cursor=5
while patch[cursor:cursor+3]!=b'EOF':
    offset=int.from_bytes(patch[cursor:cursor+3],'big');size=int.from_bytes(patch[cursor+3:cursor+5],'big');cursor+=5
    assert size>0
    applied[offset:offset+size]=patch[cursor:cursor+size];cursor+=size
assert applied==rom
assert sum(rom)&65535==struct.unpack_from('<H',rom,0xffde)[0]
metadata={'source_sha256':expected,'output_sha256':hashlib.sha256(rom).hexdigest(),'patch_sha256':hashlib.sha256(patch).hexdigest(),'changed_bytes':sum(a!=b for a,b in zip(original,rom)),'size':len(rom)}
import json
(root/'patches/raw-is-war-v3.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('ROM:',args.output)
print('IPS:',patch_path)
print(json.dumps(metadata,indent=2))
