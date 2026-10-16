"""Package the expanded 8MiB ROM and independently verified expanding IPSes."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NAME='raw-attitude-72-reference-v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def ips(before,after):
 out=bytearray(b'PATCH');i=0
 while i<len(after):
  if i<len(before)and before[i]==after[i]:i+=1;continue
  start=i
  if start==0x454f46:start-=1
  i+=1
  while i<len(after)and i-start<65535 and (i>=len(before)or before[i]!=after[i]or (i+4<len(after)and before[i:i+4]!=after[i:i+4])):i+=1
  data=after[start:i];out+=start.to_bytes(3,'big')+len(data).to_bytes(2,'big')+data
 return bytes(out)+b'EOF'
def apply(source,patch):
 out=bytearray(source);i=5;assert patch[:5]==b'PATCH'
 while patch[i:i+3]!=b'EOF':
  off=int.from_bytes(patch[i:i+3],'big');n=int.from_bytes(patch[i+3:i+5],'big');i+=5;assert n
  if len(out)<off+n:out.extend(bytes(off+n-len(out)))
  out[off:off+n]=patch[i:i+n];i+=n
 assert i+3==len(patch);return bytes(out)
def main():
 p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,default=ROOT/'build/full-roster-v1');p.add_argument('--output-dir',type=Path,default=ROOT/'downloads');a=p.parse_args();d=a.build_dir;rom=(d/(NAME+'.sfc')).read_bytes();m=json.loads((d/'manifest.json').read_text());assert sha(rom)==m['rom_sha256'];assert len(rom)==0x800000 and not m['missing_development_art'];v=json.loads((d/'runtime/validation.json').read_text());assert v['rom_sha256']==sha(rom);rope=json.loads((d/'rope-cpu/result.json').read_text());assert rope['verified_dynamic_entries']>0
 files={NAME+'.sfc':rom,'README_TR.txt':(ROOT/'assets/full-roster-v1/README_TR.txt').read_bytes(),'roster.csv':(d/'roster.csv').read_bytes()};m['patch_source_sha256']={}
 for label,path in [('from-original-sydra-v7',ROOT/'Super Fire Pro Wrestling X Premium (Japan) [T-En by Sydra v7].sfc'),('from-mankind-tie-v2',ROOT/'build/mankind-tie-v2/raw-attitude-reference-five-v2-mankind-tie.sfc')]:
  source=path.read_bytes();patch=ips(source,rom);assert apply(source,patch)==rom;files[NAME+'-'+label+'.ips']=patch;m['patch_source_sha256'][label]=sha(source)
 m['ips_expansion_roundtrips_verified']=True;files['manifest.json']=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()
 for f in ['all-84-selections.png','all-84-in-game.png','roster-gameplay.gif','roster-showcase.png','validation.json','static-validation.json','kurrgan-cpu-validation.json','kane-kurrgan-cpu.png']:
  files[f]=(d/'runtime'/f).read_bytes()
 files['rope-validation.json']=(d/'rope-cpu/result.json').read_bytes();a.output_dir.mkdir(parents=True,exist_ok=True);zpath=a.output_dir/(NAME+'.zip')
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
  for name,data in files.items():
   info=zipfile.ZipInfo(NAME+'/'+name,(2026,10,16,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
 with zipfile.ZipFile(zpath)as z:assert z.testzip()is None and sha(z.read(NAME+'/'+NAME+'.sfc'))==sha(rom)
 report={'zip_sha256':sha(zpath.read_bytes()),'rom_sha256':sha(rom),'zip_bytes':zpath.stat().st_size,'manifest':m};(a.output_dir/(NAME+'-release.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(a.output_dir/(NAME+'.sha256')).write_text(report['zip_sha256']+'  '+zpath.name+'\n'+sha(rom)+'  '+NAME+'.sfc\n');print(json.dumps({k:v for k,v in report.items()if k!='manifest'},indent=2))
if __name__=='__main__':main()
