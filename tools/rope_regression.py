"""Exercise rope rebounds and verify every updated rope graphic against the original."""
import argparse
import ctypes as C
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image
from headless_snes import Emulator

parser=argparse.ArgumentParser()
parser.add_argument('--rom',type=Path,required=True)
parser.add_argument('--core',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--ring',choices=('HWA','HWF','RANDOM'),default='HWA')
parser.add_argument('--cpu',action='store_true')
parser.add_argument('--frames',type=int,default=20000)
parser.add_argument('--capture-baseline',type=Path,help='Extract original ring graphics, then exit without claiming a test pass')
parser.add_argument('--record-gif',action='store_true')
args=parser.parse_args()
args.output_dir.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[1]
baseline=(root/'assets/raw-ring/hwa-baseline.bin').read_bytes()
references=[('HWA',(baseline[:0x4000],(root/'assets/raw-ring/hwa-bg2-baseline.bin').read_bytes()))]
# V3 deliberately uses HWA's original geometry for every arena choice.
e=Emulator(args.rom,args.core)
e.run(1200);e.press('start');e.run(150);e.press('down');e.press('b');e.run(150)
if args.cpu:e.press('right');e.press('right')
if args.ring!='HWA':
    for _ in range(4):e.press('down')
    for _ in range(('HWA','HWF','RANDOM').index(args.ring)):e.press('right')
e.image(args.output_dir/'options.png')
e.press('start');e.run(450);e.press('b');e.run(45);e.press('b');e.run(150)
e.press('b');e.run(45);e.press('right');e.press('b');e.run(45);e.press('b');e.run(600);e.press('b');e.run(900)
e.image(args.output_dir/'start.png')
ptr=e.core.retro_get_memory_data(3)
def vram():return C.string_at(ptr,0x10000)
initial=vram();initial_maps=np.frombuffer(initial[0x7000:0x8000],'<u2').copy()
if args.capture_baseline:
    args.capture_baseline.write_bytes(initial[:0x4000]+initial[0x8000:0xc000])
    print('Captured original baseline:',args.capture_baseline)
    raise SystemExit(0)
matches=[(name,ref) for name,ref in references
         if initial[:0x3000]==ref[0][:0x3000] and initial[0x8000:0xa800]==ref[1][:0x2800]]
assert matches,'Original rope graphics were changed before the test started'
reference_name,original=matches[0]
seen=set();active=0;events=0;last_active=False;frames=0;updated_cells=set()
recording=[]

def inspect():
    global active,events,last_active,frames
    raw=vram()
    # Stop at the results screen rather than interpreting its tiles as ropes.
    if raw[:0x3000]!=initial[:0x3000] or raw[0x8000:0xa800]!=initial[0x8000:0xa800]:return False
    maps=np.frombuffer(raw[0x7000:0x8000],'<u2')
    changes=np.flatnonzero(maps!=initial_maps)
    is_active=bool(len(changes))
    if is_active:
        active+=1
        if not last_active:
            events+=1
            if events<=4:e.image(args.output_dir/f'rebound-{events}.png')
    last_active=is_active
    for cell in changes:
        layer=int(cell)//1024;entry=int(maps[cell]);index=entry&1023
        updated_cells.add((layer,int(cell)%1024))
        key=layer,entry
        if key in seen:continue
        assert index+17<512,('Unexpected animation tile',layer,hex(entry))
        for small in (index,index+1,index+16,index+17):
            actual=raw[layer*0x8000+small*32:layer*0x8000+small*32+32]
            wanted=original[layer][small*32:small*32+32]
            assert actual==wanted, f'Rope graphics changed: layer={layer+1}, cell={int(cell)%1024}, entry={entry:04x}, tile={small:03x}'
        seen.add(key)
    frames+=1
    return True

if args.cpu:
    for i in range(args.frames):
        e.run(1)
        if not inspect():break
        if i%3000==2999:e.image(args.output_dir/f'frame-{i+1}.png')
else:
    with tempfile.TemporaryDirectory(prefix='sfpx-rope-') as temp:
        state=Path(temp)/'start.state';e.save(state)
        for direction in ('down','up','left','right'):
            e.load(state);last_active=False
            e.run(35,['down','right']);e.run(10)
            for _ in range(360):
                e.run(1,[direction,'x'])
                assert inspect(),'Match ended before scripted checks completed'
                if args.record_gif and direction=='down' and _%3==0:
                    recording.append(e.frame().resize((512,448),Image.Resampling.NEAREST))
            e.image(args.output_dir/f'{direction}-after.png')
            for _ in range(180):
                e.run(1)
                assert inspect(),'Match ended before recovery check'
                if args.record_gif and direction=='down' and _%3==0:
                    recording.append(e.frame().resize((512,448),Image.Resampling.NEAREST))
            e.image(args.output_dir/f'{direction}-settled.png')
assert active>0,'No rope animation executed'
e.image(args.output_dir/'end.png')
if recording:
    recording[0].save(args.output_dir/'rope-rebound.gif',save_all=True,append_images=recording[1:],duration=50,loop=0,disposal=2,optimize=True)
result={'ring':args.ring,'original_graphics_variant':reference_name,'cpu':args.cpu,'frames_checked':frames,'frames_with_map_updates':active,'animation_starts':events,'updated_rope_cells':len(updated_cells),'verified_dynamic_entries':len(seen)}
(args.output_dir/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS:',json.dumps(result))
