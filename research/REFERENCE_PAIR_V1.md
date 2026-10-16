# Stone Cold / The Rock reference revision v1

This revision is limited to roster ranks 1 and 2. The remaining 82 appearances
are unchanged from the rejected native appearance beta and need separate work.
Undertaker and the accepted RAW v3 ring remain in place. Moves, abilities, names,
portraits and selection order are retained from the preceding native beta.

## Artwork and loading

Each head model has 48 16x16 views (0x1800 bytes, 8 columns / 6 rows). BODY selects
the head resource through the 16-bit table at 0x1b15e. It does not select the
32x32 FACE portrait. Descriptors at 0x15b3b8 contain source24, length16,
destination16 and flags8. Flag 0x81 loads uncompressed heads into WRAM 7E:8000
and 7E:A000 for players 1 and 2. Unused models 8 and 9 now supply custom Austin
and Rock heads. Displaced, unused models 24 and 1 point to neutral model 0.
The builder asserts none of these four models was used by the previous roster.

Generated source sheets are quantized to the native palette. Austin has a bald
scalp, close brown goatee and thin wrist bands. Rock has a short black crew cut,
a clean-shaven face and broad black elbow pads. Both use bare chests, black
briefs, knee pads and high boots. Rock's front piping and purple/gold rear badge
are miniature pixel approximations; lettering is not legible at this resolution.
Head art covers every head view; torso, limbs and boots retain native modular
anatomy and silhouettes. This is not a complete hand-redrawn body animation set.

Actor fields C6/C8/CA/CC/CE/D0/D2 hold torso/hips/upper-arm/forearm/thigh/lower-leg/
foot collection pointers, stored as CPU address >> 8 (e.g. F5C8 = F5:C800).
D4 selects WRAM head data; D6 selects common parts. Individual arm collections
contain 128 16x16 cells (0x4000 bytes, 8 by 16 cells). Generated equipment masks
modify only the native skin pixels; Rock's hip art modifies only cloth pixels.
All native silhouettes and frame indexes are retained.

Unused collections at ROM 2FC800, 320800, 330800 and 340800 store Austin wrists,
Rock upper arms, Rock hips and Rock forearms. The builder checks all four native
costumes of all 84 profiles for prior torso/hip references before reuse.
A JSL at C1:0BEF invokes a small part-selection helper at C1:E500, overriding
only BODY 8 and 9 and preserving the original helper's register/status contract.
Unused palette slots supply independent skin, hair, silver and purple/gold shades.

## Reproduction

Python 3, Pillow and NumPy are required. Build RAW v3 with the existing ring
builder, then `python tools/build_attitude.py --base-rom build/raw-is-war-v3.sfc`.
Its native beta output must have SHA256
`77aadb605a61430b065eafa5bcb33a52dac37ca627a6a99533949b9b9f695298`.
Run `python tools/build_reference_pair.py` to create the revision.

```
python tools/smoke_reference_pair.py \
  --rom build/reference-pair-v1/raw-austin-rock-reference-v1.sfc \
  --base-rom build/attitude-native-beta/raw-attitude-84-native-beta.sfc \
  --base-manifest build/attitude-native-beta/manifest.json \
  --art-dir build/reference-pair-v1/art \
  --core /path/to/snes9x_libretro.so \
  --output-dir /tmp/reference-pair-proof
```

This cold boots the official Snes9x 1.62.3 libretro core with empty SRAM,
checks all 84 selection models, verifies exact custom head bytes and part
pointers in the actual match, directs both controllers through four runs,
three attacks and taunts, and runs an Undertaker CPU match for 1800 frames.
Only states made during that cold boot are used; no runtime appearance edits
or distributed SRAM are involved. The Windows frontend was not run here.

The old scripted rope probe was inconclusive (no rope event), so it does not
count as a pass. A separate 12000-frame CPU probe exercised 26 map cells / 18
dynamic entries and compared every referenced tile to original rope graphics.
See the published runtime and rope validation JSON. These checks cover Dream
Match; visual likeness still needs the user's review and other modes / every
move interaction are not exhaustively verified.
