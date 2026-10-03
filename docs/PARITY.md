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
| Content | Classic master reader; bounded Vilverin neighborhood packaging | Full ordered master/plugin load, overrides/deletion, world streaming, base game and installed expansions with complete dependency manifests |
| Android | Self-contained scene APK, launcher, touch controls and private QA uploads | Physical-device lifecycle, storage, installation/upgrades, controls and sustained memory/frame-time checks |
| Movement/physics | Basic traversal; native stair camera filter; fixed static Havok strips | Recover controller dimensions and motor behavior; compare run/walk/jump/swim, slopes, stairs, collision layers and dynamic bodies to the original |
| Actors/animation | TES4 names and shared-skeleton attachment; actors remain in a bind pose | Original KF sequences, skin/bone agreement, equipment slots, locomotion, attacks, first-person hands and facial animation |
| Doors/containers | Door hide toggle; base container contents can be inspected | Embedded door animation with collision and saved state; per-reference leveled inventory, locks/traps, transfer, ownership/theft and respawn |
| UI/inventory | Template HUD and native phone controls | Oblivion menus/HUD, inventory/equipment, journal/map, character creation, lockpicking and dialogue controls |
| Gameplay | Record research; no demonstrated TES4 combat or progression | Original damage/magic, skills/attributes/leveling, effects, AI/packages, crime, death and difficulty behavior |
| Scripts/quests/dialogue | No compatibility VM or validated quest progression | Bytecode/conditions, native functions, quest stages, dialogue selection, faction/reputation and representative main/side quest playthroughs |
| Audio | Phone scene starts without sound | Effects, music, voices and subtitles, including synchronized playback and mobile audio lifecycle |
| Saves/mods | No TES4 save compatibility demonstrated | Durable reference/quest/actor state, original save behavior, load/reload checks and representative mod compatibility |

Work proceeds in testable slices: finish native TES4 interaction plumbing,
recover original animation/door sequence support, implement live inventory
and equipment, then the original motor, gameplay and script/quest systems.
These priorities can overlap where a dependency is available; adding a menu
or reading a record never closes its gameplay gate.

The current packager is explicitly a bounded scene build. Its private APK
contains the whole master and its selected visual neighborhood, not the full
game’s audio, every world cell or DLC. Full content packaging and world
streaming remain required work. Do not label the current download a complete
Oblivion port or a complete-installation bundle.

Each published checkpoint needs public CTest/content-guard checks, native
build receipts, a measured local scene check where applicable, a private APK
signature/payload check, an archived recovery build and a checksum-verified
sideload download. Phone runtime acceptance is separate from Linux evidence.
