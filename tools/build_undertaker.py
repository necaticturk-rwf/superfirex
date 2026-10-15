"""Build the Ministry preset using the game's own edit SAVE routine.

Input is the accepted RAW ring v3 ROM. The original ROM is never overwritten.
The 380-byte preset is an ordinary packed SFPX edit record, not a save state.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct

from headless_snes import Emulator

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA256 = 'f3a6e07c10d3494b398d9c0c0883736f0e47f84f75113bd64adfb2629be62474'
NAME = 'raw-ministry-undertaker-v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def ips(before, after):
    patch = bytearray(b'PATCH')
    pos = 0
    while pos < len(before):
        if before[pos] == after[pos]:
            pos += 1
            continue
        start = pos
        while pos < len(before) and before[pos] != after[pos] and pos-start < 65535:
            pos += 1
        payload = after[start:pos]
        patch += start.to_bytes(3, 'big') + len(payload).to_bytes(2, 'big') + payload
    return patch + b'EOF'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-rom', type=Path, required=True)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    source = args.base_rom.read_bytes()
    assert digest(source) == BASE_SHA256, 'Use the accepted RAW ring v3 ROM.'
    rom = bytearray(source)
    # Three normal edit point ceilings (80/100/150) become 180. Skills retain
    # their native enumerations; stats retain the game's native 1..5 scale.
    for offset, old in ((0x42b0f, 80), (0x42b17, 100), (0x42b2b, 150)):
        assert struct.unpack_from('<H', rom, offset)[0] == old
        struct.pack_into('<H', rom, offset, 180)
    rom[0xffdc:0xffe0] = bytes.fromhex('ffff0000')
    checksum = sum(rom) & 65535
    struct.pack_into('<HH', rom, 0xffdc, checksum ^ 65535, checksum)
    assert sum(rom) & 65535 == checksum
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rom_path = args.output_dir / (NAME + '.sfc')
    assert rom_path.resolve() != args.base_rom.resolve()
    rom_path.write_bytes(rom)
    (args.output_dir / (NAME + '-from-raw-v3.ips')).write_bytes(ips(source, rom))

    profile = (ROOT/'assets/undertaker/ministry-v1.bin').read_bytes()
    assert len(profile) == 380
    e = Emulator(rom_path, args.core)

    def tap(key):
        e.press(key, 4)
        e.run(45)

    # A fresh SRAM image: no existing user saves are loaded or edited.
    e.run(1200)
    tap('start')
    e.run(150)
    for _ in range(6):
        tap('down')
    tap('b')
    e.run(240)
    ram = e.core.retro_get_memory_data(2)
    C.memmove(ram+0x1432, profile, len(profile))
    # Enter SKILLS to let the game initialize the edit ceiling and show the
    # preset's valid native skill values, then return to the root menu.
    tap('down')
    tap('down')
    tap('b')
    e.run(240)
    assert C.string_at(ram+0x16c0, 2) == b'\xb4\x00', 'Edit ceiling was not initialized to 180.'
    e.image(args.output_dir/'undertaker-skills.png')
    tap('select')
    e.run(240)
    assert C.string_at(ram+0x1432, len(profile)) == profile
    for _ in range(5):
        tap('down')
    tap('b')
    e.run(240)
    tap('up')  # Initial centered row is No002; choose No001.
    tap('b')
    e.run(240)
    sram = C.string_at(e.core.retro_get_memory_data(0), e.core.retro_get_memory_size(0))
    assert sram[0x62:0x62+len(profile)] == profile, 'Slot No001 was not saved.'
    assert sram[0x12] == 1, 'Slot No001 is not marked occupied.'
    assert not any(sram[0x62+380:0x62+760]), 'Unexpected second edit record.'
    sram_path = args.output_dir / (NAME+'.srm')
    sram_path.write_bytes(sram)
    e.image(args.output_dir/'undertaker-save-slot1.png')
    metadata = {
        'base_rom_sha256': digest(source), 'rom_sha256': digest(rom),
        'sram_sha256': digest(sram), 'profile_sha256': digest(profile),
        'edit_slot': 1, 'edit_point_ceiling': 180,
        'rom_changes_from_raw_v3': sum(a != b for a, b in zip(source, rom)),
        'sram_size': len(sram),
    }
    (args.output_dir/(NAME+'.json')).write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
