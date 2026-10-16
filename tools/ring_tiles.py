"""Keep every original rope tile ID; place apron art in the two retired logo areas."""
from collections import Counter, defaultdict
import struct
import numpy as np
from PIL import Image

FLIPS = ((0, lambda a: a), (0x4000, lambda a: a[:, ::-1]),
         (0x8000, lambda a: a[::-1, :]), (0xc000, lambda a: a[::-1, ::-1]))

def canonical(a):
    key, flip, b = min((f(a).tobytes(), flag, f(a)) for flag, f in FLIPS)
    return key, flip, b

def tile(data, n):
    b = data[n * 32:n * 32 + 32]
    a = np.zeros((8, 8), np.uint8)
    for y in range(8):
        for bit in range(4):
            a[y] |= np.unpackbits(np.array([b[y*2+(bit//2)*16+bit%2]], np.uint8)) << bit
    return a

def meta(data, entry):
    n = entry & 1023
    a = np.block([[tile(data, n), tile(data, n+1)], [tile(data, n+16), tile(data, n+17)]])
    if entry & 0x4000: a = a[:, ::-1]
    if entry & 0x8000: a = a[::-1, :]
    return a.copy()

def write_tile(data, n, a):
    for y in range(8):
        for bit in range(4):
            data[n*32+y*2+(bit//2)*16+bit%2] = int(np.packbits((a[y] >> bit) & 1)[0])

def write_meta(data, n, a):
    for index, small in ((n, a[:8,:8]), (n+1, a[:8,8:]), (n+16, a[8:,:8]), (n+17, a[8:,8:])):
        write_tile(data, index, small)

def rgb5(words):
    words = np.asarray(words, dtype=np.int32)
    return np.stack((words & 31, (words >> 5) & 31, (words >> 10) & 31), axis=-1)

def build_geometry(rom, original, baseline, bg2, logo_path):
    bg1 = bytearray(baseline[:0x4000])
    original_bg2 = bytes(bg2)
    bg2 = bytearray(bg2)
    entries1 = list(struct.unpack('<1024H', baseline[0x4000:0x4800]))
    entries2 = list(struct.unpack('<1024H', baseline[0x4800:0x5000]))
    # A few mat-logo-area blocks are also used by posts and borders. Preserve
    # their original IDs and bytes rather than treating the whole area as free.
    reserved_bg2 = {e & 1023 for e in entries2
                    if 320 <= (e & 1023) < 512 and ((e >> 10) & 7) != 4}
    slots_bg2 = [320+(j//8)*32+(j%8)*2 for j in range(48)
                 if 320+(j//8)*32+(j%8)*2 not in reserved_bg2]
    palettes = {p: list(struct.unpack_from('<16H', rom, 0x1e07d+(p-4)*32)) for p in range(4, 8)}
    old_p4 = palettes[4]
    def grey(n): return n | (n << 5) | (n << 10)
    # Preserve apron colors and add the grays needed for underlying ring geometry.
    colors = old_p4[:10] + [old_p4[13], palettes[5][3], palettes[5][1], grey(20), grey(12), grey(25)]
    target_rgb = rgb5(colors)
    def quantize(rgb, opaque):
        distances = ((rgb[...,None,:] - target_rgb[None,None,1:,:]) ** 2).sum(axis=-1)
        out = (distances.argmin(axis=-1) + 1).astype(np.uint8)
        out[~opaque] = 0
        return out
    logo = Image.open(logo_path).convert('RGB')
    image = np.asarray(logo); ys, xs = np.where(image.max(axis=2) > 85)
    logo = np.asarray(logo.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)).resize((144,25),Image.Resampling.LANCZOS))
    letters = np.where((logo[:,:,0]>65)&(logo[:,:,1]<100),1,np.where(logo.min(axis=2)>95,3,0)).astype(np.uint8)
    # The center logo's BG2 graphics are no longer referenced by the mat.
    for i, entry in enumerate(entries2):
        if ((entry >> 10) & 7) == 4 and 0x140 <= (entry & 1023) < 0x200:
            entries2[i] = 0x1422
    cells = {}; patterns = {}; composites = {}; groups = defaultdict(set)
    for i, entry in enumerate(entries1):
        if ((entry >> 10) & 7) != 7: continue
        a = meta(bg1, entry); a[(a == 11) | (a == 12)] = 9
        for dy in range(16):
            for dx in range(16):
                x = i % 32 * 16 + dx; y = i // 32 * 16 + dy
                if x < 256: u = x-96; top = 245+(x-80)*120/176+10
                else: u = x-272; top = 365-(x-256)*120/176+10
                ly = int(y-top)
                if 0 <= u < 144 and 0 <= ly < 25 and a[dy,dx] and letters[ly,u]:
                    a[dy,dx] = letters[ly,u]
        opaque = a != 0
        a = quantize(rgb5(old_p4)[a], opaque)
        key, flip, pattern = canonical(a); patterns[key] = pattern
        back_entry = entries2[i]; back = meta(bg2, back_entry)
        pal = (back_entry >> 10) & 7
        if np.any(back):
            assert pal in palettes, (i, hex(back_entry))
            rgb = rgb5(palettes[pal])[back]
        else:
            rgb = np.zeros((16,16,3),np.int32)
        rgb[opaque] = target_rgb[a[opaque]]
        composite = quantize(rgb, opaque | (back != 0))
        back_key, back_flip, back_pattern = canonical(composite)
        composites[back_key] = back_pattern; groups[key].add(back_key)
        cells[i] = key, flip, back_key, back_flip
    # Up to 32 apron patterns stay on BG1; use the old BG2 mat-logo space for
    # the rest, compositing any underlying geometry before moving the cell.
    selected = set()
    remaining = set(groups)
    while remaining and len(selected) < 32:
        counts = Counter(k for group in remaining for k in groups[group])
        choice = max(sorted(remaining), key=lambda group: (sum(counts[k] == 1 for k in groups[group]), len(groups[group])))
        selected.add(choice); remaining.remove(choice)
    bg2_keys = {k for group in remaining for k in groups[group]}
    assert len(bg2_keys) <= len(slots_bg2), ('BG2 apron overflow', len(bg2_keys), len(slots_bg2))
    ids1 = {key: 384+(j//8)*32+(j%8)*2 for j,key in enumerate(sorted(selected))}
    ids2 = {key: slots_bg2[j] for j,key in enumerate(sorted(bg2_keys))}
    bg1[0x3000:0x4000] = bytes(0x1000)
    for key,index in ids1.items(): write_meta(bg1,index,patterns[key])
    for key,index in ids2.items(): write_meta(bg2,index,composites[key])
    for i,(key,flip,back_key,back_flip) in cells.items():
        if key in selected:
            entries1[i] = (entries1[i] & 0x2000) | 0x1000 | flip | ids1[key]
        else:
            entries1[i] = 0
            entries2[i] = (entries2[i] & 0x2000) | 0x1000 | back_flip | ids2[back_key]
    # All rope/post graphics, including frames absent from the initial screen,
    # retain their exact original indices and bytes on both background layers.
    assert bg1[:0x3000] == baseline[:0x3000]
    assert bg2[:0x2800] == original_bg2[:0x2800]
    for index in reserved_bg2:
        for small in (index, index+1, index+16, index+17):
            assert bg2[small*32:small*32+32] == original_bg2[small*32:small*32+32]
    assets = ((0x15b940,0x15da20,bg1[0x3000:0x4000]),
              (0x15b8c8,0x15c220,bg2[0x2800:0x4000]),
              (0x15b9a0,0x15ea20,struct.pack('<1024H',*entries1)),
              (0x15ba80,0x15f220,struct.pack('<1024H',*entries2)))
    for table,offset,data in assets:
        assert len(data) == struct.unpack_from('<H',original,table+3)[0]
        assert all(x == 255 for x in original[offset:offset+len(data)])
        rom[offset:offset+len(data)] = data
        rom[table:table+3] = (0xc00000+offset).to_bytes(3,'little')
        rom[table+7] |= 0x80
    struct.pack_into('<16H',rom,0x1e07d,*colors)
    print('Apron patterns: BG1',len(ids1),'/32; BG2',len(ids2),'/',len(slots_bg2))
