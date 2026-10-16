# 72 WWF / 12 restored originals, reference appearance revision v1

The accepted Mankind tie v2 ROM is the immutable base (SHA256
`1a9d07a5aac9170627ad3c46be2b9bc4f5375b7292103c1775b92b0c2a458526`).
The first five profile records, portraits, costume selectors and private graphics
remain unchanged. The Undertaker raw head source is relocated byte-for-byte.

67 new men use unique BODY identifiers 128–194 and raw 48-view head resources
0x200–0x242. `assets/full-roster-v1/specs.json` describes source references,
palettes and attire. `generated/heads-*.png` and `canonical-*.png` are the image
generation source sheets. Obsolete large body trials are excluded. Two canonical
outputs use clothing-only layouts, described in generation-jobs.json.

`build_full_roster.py` expands to 8 MiB ExHiROM (mapping 0x35, size 0x0D),
mirrors the reset bank at 0x400000 and writes both header checksum pairs.
New directly mapped resources stay in CPU banks 41–7D, avoiding WRAM 7E/7F.
The copied resource descriptor table is at CPU41:0000; existing descriptors
through at least 0x1CE are preserved. Raw head streams must not end at a 64 KiB
boundary: the game's loader otherwise hangs. The expanded 256-entry model
lookup is at C1:E800; its 12 references and model-index mask are patched.

The new C1:EA00 dispatch calls the accepted E700/E600/E500 helper chain first,
then sets only C6/C8/CA/CC/CE/D0/D2/D6 for new BODY128–194. D4 keeps the native
per-player head RAM pointer. Per-model eight-pointer records start at C1:EC00.
Native part streams reclaimed by earlier revisions are restored into expansion,
and native lookup tables point to those original bytes. Explicit first-five
private pointers continue to use their approved art.

`sprite_retarget.py` maps reference costume views to native modular masks with
nearest-view/mirror/rotation fitting. Native geometry, articulation and tile
ordering are retained. This is a small-pixel approximation, not newly hand-drawn
frames for every animation. Bare torso anatomy remains native; limited ink is
transferred for tattooed/hairy chests. Covered-shirt skin spill from adjacent
source arms is remapped to cloth. Some plain hips/legs and shared arm/boot gear
remain native modules with matching palette selectors. Four costume slots of
each new man intentionally use the same referenced outfit.

The 12 restored profiles are copied byte-exact from the original translated
Sydra v7 ROM, as are their portraits, portrait colors and all four costume
palette selector sets. Native body part tables resolve to original graphics.
Restorations include all previously modded women, Chyna, Vince and Shane.
They occupy the last ORIGINAL page. Other men keep their prior importance
order; Kurrgan replaces Hurricane and moves to WWF rank72. Counts are
16/16/16/16/8/12. Names are repacked within the proven native C8 name pools,
retaining the original translated font word streams for restored characters.

Kurrgan is a tall heavy POWER-counter brawler, speed2/climb1, using the existing
Big Show baseline for strength and CPU behavior, with modified attacks,
defenses and move slots. Big Boot, Big Headbutt, Chokeslam, Powerbomb, Cobra
Claw and ground Iron Claw replace the aerial Hurricane emphasis. Paralyzer
uses native standing Cobra Claw (885), not a new animation. Other WWF move
and ability bytes are preserved.

Validation uses the stock Snes9x 1.62.3 libretro core: cold empty SRAM, all84
selections, 42 pairwise matches loading every wrestler, all67 head stream
bytes and eight body pointers per new man, extended movement samples,
accepted-five private art preservation and exact original restorations.
The CPU rope test checks original dynamic rope graphics for14,000 frames.
A separate6,000-frame Kane–Kurrgan CPU bout checks the revised giant profile.
These are Dream Match checks, not an exhaustive verification of every mode,
move/rival pairing or all native alternate-color previews.

Build after producing the accepted base with the existing pair/trio/tie tools:

```
python tools/build_full_roster.py
python tools/smoke_full_roster.py --rom build/full-roster-v1/raw-attitude-72-reference-v1.sfc --manifest build/full-roster-v1/manifest.json --core /path/to/snes9x_libretro.so --output-dir build/full-roster-v1/runtime
python tools/validate_full_roster.py
python tools/rope_regression.py --rom build/full-roster-v1/raw-attitude-72-reference-v1.sfc --core /path/to/snes9x_libretro.so --output-dir build/full-roster-v1/rope-cpu --cpu --frames 14000
python tools/package_full_roster.py
```

`validate_full_roster.py` uses the local core path; adjust it for another host.
Generated source images and specs are committed so rebuilding needs no image
service. Preparation scripts document source construction; they are not needed
to rebuild, and rerunning them can replace manually curated metadata.
The package contains a ready8MiB ROM, full manifest/roster, actual game evidence,
and separately round-trip-verified expanding IPS patches from both original
Sydra v7 and accepted Mankind tie v2 ROMs. Old save-states must not be reused.
