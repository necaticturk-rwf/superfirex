"""Cold-load the Ministry SRAM, inspect its edit record, then run a CPU match."""
import argparse
import ctypes as C
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image
from headless_snes import Emulator

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--rom', type=Path, required=True)
p.add_argument('--sram', type=Path, required=True)
p.add_argument('--core', type=Path, required=True)
p.add_argument('--output-dir', type=Path, required=True)
p.add_argument('--frames', type=int, default=18000)
a = p.parse_args()
a.output_dir.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
profile = (root/'assets/undertaker/ministry-v1.bin').read_bytes()
e = Emulator(a.rom, a.core)
sram = a.sram.read_bytes()
assert len(sram) == e.core.retro_get_memory_size(0) == 32768
C.memmove(e.core.retro_get_memory_data(0), sram, len(sram))


def tap(key):
    e.press(key, 4)
    e.run(45)


def boot():
    e.run(1200)
    tap('start')
    e.run(150)


def move(slot):
    for _ in range(slot):
        tap('down')
    e.run(120)


def demo(name):
    frames = []
    for i in range(240):
        e.run(1)
        if i % 4 == 0:
            frames.append(e.frame().resize((768, 672), Image.Resampling.NEAREST))
    frames[0].save(a.output_dir/(name+'.gif'), save_all=True,
                   append_images=frames[1:], duration=67, loop=0, optimize=True)
    e.image(a.output_dir/(name+'.png'))


boot()
# Open the saved edit through the game's LOAD menu, not a save state.
for _ in range(6):
    tap('down')
tap('b')
e.run(240)
for _ in range(6):
    tap('down')
tap('b')
e.run(240)
tap('up')
tap('b')
e.run(240)
ram = e.core.retro_get_memory_data(2)
assert C.string_at(ram+0x1432, 380) == profile, 'Reloaded profile differs.'
e.image(a.output_dir/'loaded-edit.png')
for _ in range(3):
    tap('up')
tap('b')
e.run(240)
e.image(a.output_dir/'stats.png')
assert struct.unpack('<H', C.string_at(ram+0x16c0, 2))[0] == 180
tap('select')
e.run(240)
tap('down')
tap('b')
e.run(240)
move(28)
demo('chokeslam')
move(3)
demo('tombstone')
assert C.string_at(ram+0x14bd, 1) == b'\x20', 'Wrong finisher slot.'

# Reset to exercise a new match with the same persisted SRAM.
e.core.retro_reset()
boot()
tap('down')
tap('b')
e.run(150)
tap('right')
tap('right')  # CPU vs CPU
e.image(a.output_dir/'options.png')
tap('start')
e.run(450)
for _ in range(14):
    tap('r')
e.image(a.output_dir/'selection.png')
tap('b')  # Undertaker Ministry
tap('b')  # Confirm color before choosing the opponent.
for _ in range(7):
    tap('r')
tap('right')
tap('right')  # Select a built-in opponent.
tap('b')
tap('b')
tap('start')
e.run(450)
e.image(a.output_dir/'versus.png')
tap('b')
e.run(900)
e.image(a.output_dir/'match-start.png')
first = np.asarray(e.frame()).astype(int)
assert np.count_nonzero(np.max(abs(first-(205, 213, 222)), axis=2) <= 2) > 3000

vptr = e.core.retro_get_memory_data(3)
baseline = (root/'assets/raw-ring/hwa-baseline.bin').read_bytes()
bg1 = baseline[:0x4000]
bg2 = (root/'assets/raw-ring/hwa-bg2-baseline.bin').read_bytes()
initial = C.string_at(vptr, 65536)
assert initial[:0x3000] == bg1[:0x3000]
assert initial[0x8000:0xa800] == bg2[:0x2800]
initial_maps = np.frombuffer(initial[0x7000:0x8000], '<u2').copy()
seen, starts, checked, active_before = set(), 0, 0, False
movie, finish = [], False
for i in range(a.frames):
    e.run(1)
    raw = C.string_at(vptr, 65536)
    if raw[:0x3000] != initial[:0x3000]:
        finish = True  # The game has changed to its results screen.
        break
    assert raw[0x8000:0xa800] == initial[0x8000:0xa800]
    changes = np.flatnonzero(np.frombuffer(raw[0x7000:0x8000], '<u2') != initial_maps)
    active = bool(len(changes))
    starts += int(active and not active_before)
    active_before = active
    maps = np.frombuffer(raw[0x7000:0x8000], '<u2')
    for cell in changes:
        layer, entry = int(cell)//1024, int(maps[cell])
        key = layer, entry
        if key in seen:
            continue
        index = entry & 1023
        assert index+17 < 512
        for tile in (index, index+1, index+16, index+17):
            reference = (bg1, bg2)[layer][tile*32:tile*32+32]
            assert raw[layer*0x8000+tile*32:layer*0x8000+tile*32+32] == reference
        seen.add(key)
    checked += 1
    if 1800 <= i < 2760 and i % 4 == 0:
        movie.append(e.frame().resize((768, 672), Image.Resampling.NEAREST))
    if i % 2400 == 2399:
        e.image(a.output_dir/f'cpu-{i+1}.png')
if finish:
    e.run(360)
e.image(a.output_dir/'match-end.png')
assert checked >= 3000, 'Match did not advance far enough.'
assert starts > 0 and seen, 'No rope animations exercised.'
if movie:
    movie[0].save(a.output_dir/'undertaker-gameplay.gif', save_all=True,
                  append_images=movie[1:], duration=67, loop=0, optimize=True)
result = {'cold_sram_load': True, 'edit_record_roundtrip': True,
          'slot': 1, 'finisher': 'TOMBSTONE', 'critical': 'finisher',
          'stat_scale': '1..5', 'edit_points': 84, 'edit_ceiling': 180,
          'cpu_frames_checked': checked, 'reached_results': finish,
          'rope_animation_starts': starts, 'verified_rope_entries': len(seen)}
(a.output_dir/'validation.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
