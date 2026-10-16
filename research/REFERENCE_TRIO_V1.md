# Triple H, Mankind and Undertaker reference revision

This revision builds on the accepted Austin/Rock ROM. It changes appearance
fields only in ranks 3, 4 and 5. All 81 other native profiles, including Austin
and Rock, remain byte-identical. Existing names, portraits, moves and abilities
are retained. Only ranks 1–5 have individual reference revisions; the other 79
appearances remain unfinished from the earlier native beta.

## Artwork

Three new head sheets cover 48 views each. Triple H has long brown hair and a
beard; Mankind has shaggy brown hair and a leather mask; Undertaker has pale skin,
long black hair and a goatee. Costume sources and the three supplied reference
images are in `assets/reference-trio-v1`. Generated source sheets are not runtime
proof; published PNG/GIF captures come from the ROM on Snes9x 1.62.3.

Mankind has custom white collared-shirt/tie and upper-arm sleeve collections;
his forearms reuse the accepted Austin wrist-band source mask in white shades.
A separate brown leggings/pants palette allows the shirt to stay white.
Undertaker has custom black V-neck cloth, tattooed upper arms/forearms, and a
separate glove collection. The native D6 field, formerly always EE88, is the
hand collection: editing only the CC forearm cannot darken the separate hands.
Triple H uses Rock's black upper-arm pads and miniature trunk art with neutral
trim colors; white wrists and 216 lower-leg frames provide black boots and
black/white knee wraps. His approximate back motif is limited to the first five
basic angle rows; untouched native chest shading is retained elsewhere.
Tiny tattoos and emblems are approximations, not readable text or exact artwork.

## Allocation and dispatch

Models 26/28/56 were unused by the current 84 profiles. Resource IDs 61–64 were
also unreferenced by every exposed wrestler. Four obsolete compressed streams
between ROM F4984 and F7A63 supply two 0x1800-byte raw head slots at F4984 and
F6184. Resource 64 is redirected to the untouched neutral head. Undertaker's
0x1800 raw stream is at 1E7E0, ending at 1FFE0. A development allocation ending
exactly at the 64 KiB boundary hung the native loader; the shipped stream stays
inside that bank and passed cold-boot checks.

Reclaimed raw collections (CPU address >> 8):

| Pointer | Contents | Bytes |
| --- | --- | --- |
| EF08 | Mankind shirt | 4000 hex |
| F088 | Mankind sleeves | 4000 hex |
| F3C8 | Mankind wrists | 4000 hex |
| F448 | Undertaker vest | 4000 hex |
| F488 | Triple H wrists | 4000 hex |
| F588 | Undertaker tattooed upper arms | 4000 hex |
| F760 | Triple H torso/back motif | 4000 hex |
| F7CC | Undertaker forearms/gloves | 4000 hex |
| F838 | Triple H lower legs | 6C00 hex |
| F8A4 | Undertaker hands/gloves | 4000 hex |

The builder checks all four costumes of all 84 records, before and after new
appearance fields are applied, against these native table selections. It also
reserves the accepted pair's manually dispatched art. New palette slots are
checked against all 104 native faces / four costumes before assignment. Native
silhouettes and cell indexing are preserved during source quantization.

The setup tail at C1:0BEF now calls C1:E600. That helper initializes D6, dispatches
only the three new model IDs and chains the accepted pair helper at C1:E500 for
all other IDs. It preserves X/Y/DB/DP/status and returns A=EE88 as before. The
Undertaker branch overrides D6 after initialization. The old helper and all
Austin/Rock head/arm/hip resources stay unchanged.

## Reproduction and verification

Rebuild RAW v3, native beta and the accepted pair with their existing builders;
then run `python tools/build_reference_trio.py`. Python 3, Pillow and NumPy are
required. `tools/smoke_reference_trio.py --help` lists ROM, base-manifest, art/core
and output arguments. It cold boots with empty SRAM, checks all 84 selection
models and page counts, verifies custom head bytes and part pointers for all
five updated characters in three 1P-vs-2P matches, exercises new characters'
four run directions / three attacks / taunts, then runs a 3600-frame CPU match.
Only save states produced by the same cold boot are used; no runtime appearance
writes or distributed SRAM are involved. The separate 12000-frame rope CPU
probe checks referenced dynamic graphics against original rope tiles.

The Windows frontend, other match modes and exhaustive moveset interactions
were not run. Visual resemblance remains for the user to assess. See the
published runtime/rope JSON and real-game PNG/GIF evidence.
