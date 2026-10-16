"""Exercise the new Kurrgan profile in an unattended CPU bout."""
from pathlib import Path
import ctypes as C,json,struct
import numpy as np
from headless_snes import Emulator
ROOT=Path(__file__).resolve().parents[1];d=ROOT/'build/full-roster-v1';out=d/'runtime';e=Emulator(d/'raw-attitude-72-reference-v1.sfc','/tmp/sfpx-snes9x-1.62.3/libretro/snes9x_libretro.so')
def tap(k):e.press(k,4);e.run(150 if k=='b'else 45)
def ram():return C.string_at(e.core.retro_get_memory_data(2),131072)
def word(at):return struct.unpack_from('<H',ram(),at)[0]
def cursor(target):
 current=word(0x1887)&255
 for _ in range(abs(target//4-current//4)):tap('down'if target//4>current//4 else'up')
 for _ in range(abs(target%4-current%4)):tap('right'if target%4>current%4 else'left')
 assert word(0x1887)&255==target
m=json.loads((d/'manifest.json').read_text());k=next(s for s in m['appearances']if s['target_name']=='Kurrgan')
e.load(out/'options.state');e.run(1);tap('right');tap('right');tap('start');e.run(450);cursor(5);tap('b');tap('b')
for _ in range(4):tap('r')
cursor(7);tap('b');tap('b');tap('start');e.run(450);tap('b');e.run(1140)
assert ram()[0xa000:0xb800]==(d/'art/kurrgan-heads.bin').read_bytes();e.image(out/'kane-kurrgan-cpu-start.png');start=np.array(e.frame());positions=set()
for i in range(6000):
 e.run(1)
 if i%30==0:positions.add((word(0xa79),word(0xa7d),word(0xb7d),word(0xb81)))
assert len(positions)>30 and not np.array_equal(start,np.array(e.frame()));e.image(out/'kane-kurrgan-cpu.png');report={'rom_sha256':m['rom_sha256'],'bout':['Kane','Kurrgan'],'cpu_frames_after_intro':6000,'unique_sampled_positions':len(positions),'kurrgan_head_stream_verified':True,'moves':k['moves'],'attack':k['attack'],'defense':k['defense'],'finisher':k['finisher'],'limitation':'Ordinary AI bout; not every move forced individually.'};(out/'kurrgan-cpu-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS Kurrgan CPU',len(positions),flush=True)
