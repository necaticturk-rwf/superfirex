# Native Attitude roster beta

Status: playable 84-slot beta; individual in-ring artwork remains unfinished.

The ROM contains 104 packed native profiles of 298 bytes at 0x48481. The approved mapping uses 84 unique profiles; this corrects the earlier inference that there were only 84 native profiles. The other 20 profiles are not exposed in the six-page menu.

Name resource IDs occupy profile offsets 280/282/284. Costume descriptors occupy offsets 286–297. Portrait FACE IDs remain unique; BODY IDs can be retargeted independently. Native palette selectors are at 0x5d07e + FACE*32 + costume*8, and refer to eight category-specific RGB555 shade tables. Native portrait graphics are 32x32, 16 SNES 4bpp tiles at 0x70000 + FACE*512; 14 opaque palette words begin at 0xf3d44 + FACE*28, mapping to indices 1–14. Index 0 is transparent.

Group pointer tables: 0x481eb, normal-order pointers 0x482d9, normal/unlocked group counts 0x481cd/0x481dc. Two unused native records (8 and 9) hold six padded 16-slot pointer/order lists. The two obsolete pointers to those records are redirected before reuse. Both count tables expose 16/16/16/16/16/4. The promotion-count helper at 0x29156 returns six and omits old EDIT/unlock groups. Positive resource offsets are required by all name consumers; a discarded negative-bank pool rendered the first page but crashed on page changes. Current names use free 0x3ff800 space and the reclaimed 0x82a65–0x834e1 native-name area; unused native names point to RESERVE placeholders.

The live WRAM selected ID at 0x1887 establishes source mappings without guessing the custom display order. WRAM 0x17fd caches the BODY ID, not the portrait FACE ID. The selected FACE and BODY happened to match in the original ROM, which initially obscured the distinction.

The builder preserves the accepted RAW v3 ring region and animation tile IDs. Native profiles carry 57 move IDs, a finisher-slot byte, packed 1–5 attack/defense values, native skill enumerations and CPU templates with customized approach/late-grapple weights. The native edit point limit is not changed by this release.

Portraits were generated for this mod and converted to 32x32/14 opaque colors. New portrait art does not imply newly drawn in-ring head/body art. Female profiles retain provisional slim native body parts. See the release README and per-character finisher representation table for remaining scope.

Validation: empty-SRAM cold boot on the official 1.62.3 core; all 84 live native IDs/BODY IDs checked; 84 match loads; 117600 subsequent CPU frames, eight 9000-frame samples and 76 600-frame samples; L/R wrapping, last-page bounds and old Undertaker SRAM checked. The random-button probe kept IDs in range but observed only two distinct IDs, so it does not establish full random-selection coverage. The old controlled rebound script produced no animation event with this lineup and was inconclusive. The CPU route exercised 106 changed ring cells / 69 unique dynamic entries across 24000 frames and compared every referenced rope tile against original graphics. Other modes and exhaustive individual move interactions remain untested.

Rebuild with `python tools/build_attitude.py --base-rom build/raw-is-war-v3.sfc`. Exercise the final output with `python tools/smoke_attitude.py --rom build/attitude-native-beta/raw-attitude-84-native-beta.sfc --manifest build/attitude-native-beta/manifest.json --core /path/to/snes9x_libretro.so --output-dir /tmp/attitude-proof --all-matches`. The smoke runner uses states created during its own cold boot; no pre-mod states or runtime memory writes supply the roster.
