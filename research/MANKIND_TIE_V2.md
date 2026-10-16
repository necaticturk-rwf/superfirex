# Mankind closed shirt and tie correction

The accepted first-five v1 ROM remains the base. Its Mankind chest had a tie,
but the native XL suit abdomen (F548) overlaid it with a brown singlet pattern
and white edges. Together these read as an open shirt or braces. The correction
replaces both chest and abdomen clothing textures with a closed white collared
shirt and a narrow dark tie over a brown trouser waistband.

The head/mask, arms, legs, boots, palette, native profile, moves, abilities and
all four other accepted appearances stay unchanged. Pixel-level details are
limited by native 16x16 part cells. Original silhouettes and animation indexes
are retained. Source atlases are in assets/mankind-tie-v2; published proof comes
from the built ROM, not these source sheets.

Mankind's existing private chest slot EF08 is updated. His private abdomen now
uses F9E8, the first 0x4000 bytes of an unused 0x6c00 large-thigh collection.
The builder checks that none of the 84 profiles' four native costumes selects
that collection. Shared F548 stays unchanged, protecting other wrestlers.
A 27-byte helper at C1:E700 calls the accepted dispatcher C1:E600, then changes
only BODY 28's C8 pointer to F9E8; all other models retain the dispatcher's
results. The status/register return contract and Undertaker's D6 hands stay
intact. The helper does not overlap the head stream at C1:E7E0.

The output differs from v1 only at the ROM checksum, six-byte setup call,
new helper, private chest and new abdomen slot. The builder asserts that exact
byte-change allowlist and checks all 84 native records remain identical. Ring,
head, palette and other character graphics are therefore preserved.

Rebuild the accepted first-five v1 through its existing pipeline, then run
`python tools/fix_mankind_tie.py`. Run the existing smoke_reference_trio.py on
the new ROM/art directory; its appearance manifest supplies the added Mankind
C8 pointer check. This cold boots empty SRAM, checks all 84 selections, verifies
all five new head/part sources in three 1P-vs-2P matches, captures four runs /
three attacks / taunts for the trio and runs a 3600-frame CPU match.

The existing first-five v1 rope test applies to unchanged ring graphic bytes;
this small correction does not claim another 12000-frame rope probe. Other
match modes and every move interaction were not exhaustively tested.
