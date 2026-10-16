"""Build a verified ready-ROM / IPS / actual-game-evidence ZIP for the first five."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from build_undertaker import ips

ROOT=Path(__file__).resolve().parents[1]
NAME='raw-attitude-reference-five-v1'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--original',type=Path,required=True);p.add_argument('--base',type=Path,required=True)
p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True)
p.add_argument('--rope-result',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
a=p.parse_args();rom=(a.build_dir/(NAME+'.sfc')).read_bytes();manifest=json.loads((a.build_dir/'manifest.json').read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def apply(source,patch):
 result=bytearray(source);assert patch[:5]==b'PATCH';i=5
 while patch[i:i+3]!=b'EOF':
  off=int.from_bytes(patch[i:i+3],'big');length=int.from_bytes(patch[i+3:i+5],'big');i+=5
  if length:data=patch[i:i+length];i+=length
  else:
   count=int.from_bytes(patch[i:i+2],'big');data=patch[i+2:i+3]*count;i+=3
  result[off:off+len(data)]=data
 assert i+3==len(patch);return bytes(result)
assert manifest['rom_sha256']==sha(rom)
validation=json.loads((a.proof_dir/'validation.json').read_text());assert validation['rom_sha256']==sha(rom)
files={NAME+'.sfc':rom,'README_TR.txt':(ROOT/'assets/reference-trio-v1/README_TR.txt').read_bytes()}
manifest['patch_source_sha256']={}
for label,path in [('from-austin-rock-v1',a.base),('from-original-sydra-v7',a.original)]:
 source=path.read_bytes();patch=ips(source,rom);assert apply(source,patch)==rom
 files[NAME+'-'+label+'.ips']=patch;manifest['patch_source_sha256'][label]=sha(source)
manifest['ips_roundtrips_verified']=True
for file in ['reference-trio-in-game-views.png','reference-trio-gameplay.gif','hhh-selection.png',
             'mankind-selection.png','undertaker-selection.png','hhh-mankind-cpu.png','validation.json']:
 files[file]=(a.proof_dir/file).read_bytes()
files['rope-validation.json']=a.rope_result.read_bytes();files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
a.output_dir.mkdir(parents=True,exist_ok=True);path=a.output_dir/(NAME+'.zip')
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for name,data in files.items():
  info=zipfile.ZipInfo(NAME+'/'+name,(2026,10,16,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
with zipfile.ZipFile(path)as z:assert z.testzip() is None and sha(z.read(NAME+'/'+NAME+'.sfc'))==sha(rom)
report={'zip_sha256':sha(path.read_bytes()),'rom_sha256':sha(rom),'zip_bytes':path.stat().st_size,'manifest':manifest}
(a.output_dir/(NAME+'-release.json')).write_text(json.dumps(report,indent=2)+'\n')
(a.output_dir/(NAME+'.sha256')).write_text(report['zip_sha256']+'  '+path.name+'\n'+sha(rom)+'  '+NAME+'.sfc\n')
print(json.dumps({k:v for k,v in report.items()if k!='manifest'},indent=2))
