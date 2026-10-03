# Classic Oblivion Android parity

Owner instruction, 2026-10-03: continue the interrupted implementation, publish
finished source and documentation to GitHub, provide private asset-packed test
APKs on the existing sideload server, and keep advancing toward a 1:1 Android
port. This supersedes earlier notes that treated one-to-one gameplay as an
optional future target. It does not establish parity for any existing feature.

The local classic installation is available for private data inspection and,
when needed, executable analysis. Publish independently implemented behavior
and measurements, with proprietary code and extracts kept outside the public
repository. Reuse the audited readers/renderer where useful. TES3 formulas,
placeholder bodies and template UI are not evidence of TES4 equivalence.

| Area | Present checkpoint | Parity acceptance |
|---|---|---|
| Content | Classic master reader; bounded Vilverin APK and a complete installed-Data APK set with file manifests | Full ordered master/plugin semantics, overrides/deletion, world streaming and expansion gameplay |
| Android | Scene APK, complete signed APK-set packaging, launcher, touch controls and private QA uploads | Physical-device lifecycle, storage, installation/upgrades, controls and sustained memory/frame-time checks |
| Movement/physics | Basic traversal; native stair camera filter; fixed static Havok strips | Recover controller dimensions and motor behavior; compare run/walk/jump/swim, slopes, stairs, collision layers and dynamic bodies to the original |
| Actors/animation | TES4 transform KF decoding, constant/spline channels and default NPC idle with live shared skinning; measured desktop loops | Original-executable animation agreement, equipment slots, locomotion, attacks, first-person hands and facial animation |
| Doors/containers | Original embedded Vilverin Open/Close clips and authored moving boxes; desktop closed/open/closed collision and player traversal pass; base container inspection | Phone gate acceptance, original reversal/obstruction behavior and saved state; per-reference leveled inventory, locks/keys/traps, transfer, ownership/theft and respawn |
| UI/inventory | Template HUD and native phone controls | Oblivion menus/HUD, inventory/equipment, journal/map, character creation, lockpicking and dialogue controls |
| Gameplay | Record research; no demonstrated TES4 combat or progression | Original damage/magic, skills/attributes/leveling, effects, AI/packages, crime, death and difficulty behavior |
| Scripts/quests/dialogue | No compatibility VM or validated quest progression | Bytecode/conditions, native functions, quest stages, dialogue selection, faction/reputation and representative main/side quest playthroughs |
| Audio | Native audio enabled; original door sounds packaged and identified in desktop engine output | Phone audio acceptance, original attenuation, effects/footsteps, music selection, voices/subtitles, synchronization and mobile audio lifecycle |
| Saves/mods | No TES4 save compatibility demonstrated | Durable reference/quest/actor state, original save behavior, load/reload checks and representative mod compatibility |

Work proceeds in testable slices: finish native TES4 interaction plumbing,
recover original animation/door sequence support, implement live inventory
and equipment, then the original motor, gameplay and script/quest systems.
These priorities can overlap where a dependency is available; adding a menu
or reading a record never closes its gameplay gate.

The smaller single APK remains a bounded scene build. The separate
`--all-assets` package includes every file from the supplied Data directory,
including installed expansions, audio and video. The measured 5.50 GB
compressed Data exceeds the single signed APK format; a signed APK set carries
the complete installation snapshot. See [installed assets](research/INSTALLED_ASSETS.md).
World streaming and gameplay parity remain required work. Do not label either
download a complete Oblivion port.

Each published checkpoint needs public CTest/content-guard checks, native
build receipts, a measured local scene check where applicable, a private APK
signature/payload check, an archived recovery build and a checksum-verified
sideload download. Phone runtime acceptance is separate from Linux evidence.
