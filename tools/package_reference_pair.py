"""Package the two-character revision, verifying both IPS routes independently."""
from pathlib import Path
import argparse,hashlib,json,zipfile
from build_undertaker import ips
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--original',type=Path,required=True);p.add_argument('--base',type=Path,required=True)
p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True)
p.add_argument('--rope-result',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
a=p.parse_args();name='raw-austin-rock-reference-v1';rom=(a.build_dir/(name+'.sfc')).read_bytes();report=json.loads((a.build_dir/'manifest.json').read_text())
def sha(x):return hashlib.sha256(x).hexdigest()
def apply(source,patch):
 result=bytearray(source);assert patch[:5]==b'PATCH';i=5
 while patch[i:i+3]!=b'EOF':
  offset=int.from_bytes(patch[i:i+3],'big');length=int.from_bytes(patch[i+3:i+5],'big');i+=5
  if length:data=patch[i:i+length];i+=length
  else:
   count=int.from_bytes(patch[i:i+2],'big');data=patch[i+2:i+3]*count;i+=3
  result[offset:offset+len(data)]=data
 assert i+3==len(patch)
 return bytes(result)
files={name+'.sfc':rom,'README_TR.txt':(a.build_dir/'README_TR.txt').read_bytes()}
patch_sources={}
for label,path in [('from-native-beta',a.base),('from-original-sydra-v7',a.original)]:
 source=path.read_bytes();patch=ips(source,rom);assert apply(source,patch)==rom
 files[name+'-'+label+'.ips']=patch;patch_sources[label]=sha(source)
for file in ['reference-pair-in-game-views.png','reference-pair-gameplay.gif','austin-selection.png','rock-selection.png','pair-match.png','validation.json']:
 files[file]=(a.proof_dir/file).read_bytes()
files['rope-validation.json']=a.rope_result.read_bytes();report['patch_source_sha256']=patch_sources;report['ips_roundtrips_verified']=True
files['manifest.json']=(json.dumps(report,indent=2)+'\n').encode();a.output_dir.mkdir(parents=True,exist_ok=True)
zip_path=a.output_dir/(name+'.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for file,data in files.items():
  info=zipfile.ZipInfo(name+'/'+file,(2026,10,16,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
checks={'zip_sha256':sha(zip_path.read_bytes()),'rom_sha256':sha(rom),'zip_bytes':zip_path.stat().st_size,'manifest':report}
(a.output_dir/(name+'-release.json')).write_text(json.dumps(checks,indent=2)+'\n')
(a.output_dir/(name+'.sha256')).write_text(sha(zip_path.read_bytes())+'  '+zip_path.name+'\n'+sha(rom)+'  '+name+'.sfc\n')
print(json.dumps({k:v for k,v in checks.items()if k!='manifest'},indent=2))
