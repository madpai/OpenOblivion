# Project review and continuation plan

Date: 2026-10-06 (state: builds up to `0.44-menu-exit`, 62 commits in seven days). This review reads the
repository, its tests, the packaged APK, the owner workspace layout and the retail executable/data with the new
recon tools (compendium: `re-binary-recon`, `bethesda-gamebryo-re`). It separates **measured** statements from
**judgement**. Nothing here changes the project's rules: private data stays private, parity claims need evidence.

## 1. Verdict

The engineering evidence discipline is unusually good: hash-locked native "receipts", a fact/inference ledger, formulas
decoded from the original executable, console and runtime-memory measurements of the original game, 7,943 of 7,945
scripts matching the game's own bytecode, a public-content guard, and honest "this is not parity" wording. A playable
Vilverin slice plus an explorable open world exists in a week.

What holds the project back is not code quality in any single feature. It is five structural problems:

1. **The feedback loop is one human and one phone.** Builds 0.40-0.44 (about twenty features) have never been run on
   the device; the emulator cannot render; there is no `adb`. Every round trip costs hours and a 290 MB install.
2. **The engine foundation is split in two.** Desktop probes run OpenMW `46bd459` (Lua API rev 160), the phone runs a
   donor at `f4bec41` (Lua rev 129). Every receipt is patched twice. Desktop evidence does not prove phone behaviour.
3. **The NPC bridge has a ceiling** that the next features (AI packages, magic, animation groups, actor values) cannot
   pass: 34% of the call sites in the game's own scripts need subsystems the bridge cannot express.
4. **The UI is hand-built**, while the original UI is data-driven (104 XML files in `Oblivion - Misc.bsa`).
5. **Documents contradict the code.** The README stops at 0.22, the agent brief says gait is unmeasured though it is
   implemented, the roadmap still asks for an authoritative co-op slice first. A fresh agent starts from false facts.

Everything below is a fix sketch for these, plus a per-feature table and a phased plan.

## 2. What to keep (do not "fix")

- Receipts with hash locks and per-target patches; the rule "edit patched copies, regenerate the patch".
- Evidence tiers in every research doc; the PARITY ledger idea (the content just went stale).
- Measuring the original: Proton run + `/proc/<pid>/mem` sampler (player hull), console values, executable formulas.
- Real-data assertions (compile every script and compare opcode sequences) and fixtures that run in CTest.
- Private-data boundary: generated at package time, `content_guard.py`, no assets in CI.
- Fail-open object scripts, one-time logging of unimplemented commands, tap logging, crash backtrace, BACK button.
- Version-tagged slices with a recovery build.

## 3. Findings (what went wrong, with evidence)

| # | Sev | Finding | Evidence | Root cause |
|---|---|---|---|---|
| F1 | P0 | No automated device loop; 0.40-0.44 unverified on the phone | HANDOFF: "owner has not yet tested 0.40-0.43"; ANDROID.md: emulator crashes in the ARM translation layer, "no physical device was connected to ADB"; `adb` is not installed on the build host | Phone testing was designed as a manual QA page, not a scripted gate |
| F2 | P0 | Two engine vintages; every receipt exists twice | `upstreams.lock.json`: OpenMW `46bd459` vs donor `f4bec41`; 8 `*_desktop.patch` + 8 `*_android.patch` (about 2,370 lines, near-identical sizes); Lua overlay must run on API 160 and 129; memory/notes: "Android and desktop can differ" | The Android baseline is a third-party release (OpenMW-Android 0.51-11) while desktop tracks master |
| F3 | P0 | CI never builds the patched engine or an APK; one build host, known bad RAM | `ci.yml` builds only `src/` (241 lines) and runs fixtures; a cached payload part was corrupted on this host during testing | Heavy builds live in a private workspace |
| F4 | P1 | 292 MB APK per update | `unzip -l`: embedded `payload-000.zip` 236 MB (the master) + `libopenmw.so` 133 MB uncompressed (symbol table kept) | The master and symbols ship inside the APK; overlay Lua is bundled with them |
| F5 | P1 | Stale and contradictory docs | README "New in 0.22-body"; AGENTS.md "gait, run speed and step height remain unmeasured" vs TES4_MOVEMENT.md "Original formula (measured)" and the `tes4_movement` receipt; PLAYER_MOVEMENT "speed stays blocked"; ARCHITECTURE "only the reader wrapper exists"; PARITY "no compatibility VM or validated quest progression"; HANDOFF "implement a co-op slice before broad TES4 combat/quest conversion"; HANDOFF is 453 lines of chronology | State is written in prose in five places; no single source of truth |
| F6 | P1 | Bridge ceiling | Actor proxy = copy of the template player record, TES4 id smuggled in the unused `head` field; host AI, host stats, 5,411 generated host item records; script coverage below | Bridge was the fastest way to get collision, pathfinding and death from the host |
| F7 | P1 | Hand-built UI instead of the original data-driven menus | `Oblivion - Misc.bsa` holds `menus/*.xml` (104 files, 1.22 MB, 570 tag names, 40 tags cover almost all), including `negotiate_menu.xml`, `persuasion_menu.xml`, `lockpick_menu.xml`, `container_menu.xml`, `levelup_menu.xml`; the exe has `Tile`, `TileMenu`, `TileRect` and ~38 `*Menu` classes | UI was built per screen to unblock testing |
| F8 | P1 | Script runtime guesses and silent wrong answers | Object scripts tick every 0.25 s (no source); unimplemented commands return 0; 65 implemented commands cover 65.9% of 32,677 call sites; a missing command that *returns a value* silently changes conditions | Runtime written feature-first |
| F9 | P2 | Flag sprawl | about 30 `OPENOBLIVION_*` switches (`ORIGINAL_BODY`, `TES4_MOVEMENT`, `AUTHORED_COLLISION`, `GROUNDED_EYE`, `TES4_PLAYER`, `TES4_COMBAT`, `TES4_TREES`, `DOOR_*`...); phone builds run exactly one combination | Each receipt shipped dark behind an env flag |
| F10 | P2 | Work ordering | Faces, hair, doors, trees were done before actor values, AI packages, magic, saves; the sideload release notes say "a world you can explore rather than a playable game" | Visible wins first |
| F11 | P2 | Several rules rest on documentation, not on the executable | topic-list rule, leveled-list rules, say-once, `GetInCell` dummy cells, object script cadence | The exe was only read for formulas; class names were unavailable (now: full RTTI) |
| F12 | P2 | Rendering path unmeasured | Collada loader failures on Android, single-threaded OSG workaround, GL4ES (desktop GL 2.1 emulated on GLES); no systematic frame-time/memory telemetry | No device loop (F1) |

## 4. New facts from this review (measured, safe to rely on)

- **Quest script delay is verified**: the INI setting `fQuestScriptDelayTime` ships with default 5.0 in
  `Oblivion_default.ini` (the runtime's 5 s was a guess, now sourced). The same file has `bActivateAllQuestScripts=0`.
  There is **no** object-script delay setting: the 0.25 s object tick remains unverified.
- **Persuasion/barter/disposition constants are recoverable** from the executable's setting defaults plus the master
  (dozens of persuasion settings, barter disposition modifiers, `fDispositionReduction`, bribe/demand scales, greeting
  and conversation distances). Regenerate locally with `gmst_defaults.py`; do not commit the table.
- **Script command coverage**: of 32,677 command call sites in the compiled master, 195 distinct unimplemented
  commands account for 11,141 sites. By subsystem (regex bucketing, approximate): AI packages and behaviour 22.9%
  (`EvaluatePackage` 1,163, `AddScriptPackage` 275, `SetAlert`, `Look`), magic and effects 15.2% (`RemoveSpell` 600,
  `Cast` 339, `AddSpell` 290), animation 13.0% (`PlayGroup` 841, `PickIdle`, `IsAnimPlaying`), speech and sound 10.9%
  (`Say` 529, `SayTo` 318), combat 10.9% (`StartCombat` 308, `SetEssential` 279), world/object state 8.8%, actor
  values 8.2% (`SetActorValue` 416).
- **UI is data**: menus are XML expression trees (`copy`, `ref`, `include`, `add/sub/mul/div`, `eq`, `onlyif`,
  `user0..N`, `clicked`) over DDS art; strings in `strings.xml`; the C++ menu classes only fill user traits.
- **Movement speed is already decoded** and implemented (`tes4_movement`): the earlier recon note that GMST defaults
  "settle" movement overstated it. Still unmodelled: carried weight, swim speed, jump height, sneak camera,
  athletics/acrobatics progression.

## 5. Fix sketches for everything built so far

Format: feature, what is wrong or unproven, fix, oracle that proves the fix.

| Feature | Problem | Fix sketch | Oracle |
|---|---|---|---|
| Foundation readers (`inspect`, scans) | none significant | add property tests on random mutations; keep | existing fixtures |
| Receipts / patch stack | doubled per vintage; flags | one engine revision (section 6, step 0.2); one shared `.hpp` per receipt, thin per-target glue; one feature profile instead of ~30 env switches | CI `patch --dry-run` on the pin; desktop probe built from the phone's revision |
| Android host and packaging | 292 MB per update; master and symbols in APK | strip the shipped lib (keep unstripped copy private, print build-id + module offsets in crashes and symbolicate offline); move the master into the data payload; add a hot-overlay channel (Lua + generated `tes4data` as a small signed zip fetched from the sideload server at launch, version-checked) | APK under 40 MB; overlay-only update under 20 MB; payload hashes unchanged |
| Download/payload system | works (resume, SHA256) | keep; add a "verify installed data" button using the manifest | all 824 hashes |
| Build host integrity | bad RAM can corrupt builds and caches | replace the stick; until then build twice and compare hashes, verify payload hashes after copy | identical SHA256 on two builds |
| Player body, stairs, camera | 0.22-0.44 unconfirmed on phone; step height, slope limit, jump impulse, race scale unmeasured; measured hull-to-floor float not reproduced | run the Proton sampler (it exists) over stairs/slope/jump/race scale and fit the controller; reproduce the float; keep 0.5 camera filter until then | sampler traces vs desktop probe traces |
| Movement and gait | formula implemented; encumbrance, swim, jump height, sneak camera, skill progression missing | load an **effective settings table** (master record if present, else executable default) as `tes4data/settings.lua` and drive movement, jump, swim, fall damage and weight from it | sampler speeds; console values |
| Collision (`OL_STATIC` strips, authored triangles) | phone acceptance pending; dynamic bodies and collision layers absent | accept on phone via device gate; later map Havok layers to Bullet masks | stair/ramp/gate regressions |
| Player/NPC rendering (`tes4_player`) | no FaceGen morphs (EGM), no female/beast races, no bare body under armour; hair/face texture hacks | implement EGM/FGTS in a native module; model race/body slots from RACE; stop per-feature texture hacks | screenshot diff vs Proton captures |
| NPC bridge | smuggled `head` field; Morrowind-shaped host actor; host AI | introduce a native `Tes4Actor` component (record id, race, stats, process level, package state) that the bridge sets explicitly; keep the proxy as a collision/pathing shim only; drive AI from TES4 packages (phase 4) | actor state dump vs original console |
| Items, inventory, loot | host records; no enchantments, condition, gold as currency, scripts | after the menu interpreter, own the item model in Lua; keep generated records as a shim; verify leveled lists against the executable | leveled-list roll counts vs console |
| Combat | hand-to-hand and weapons/armor formulas from exe; no block, power attack, fatigue per swing, bows, stagger, difficulty, magic | decode the damage routine and the weapon attack functions; add fixtures with console-measured values; implement blocking, power attacks, bows; then spells | per-hit damage vs console |
| Animation | KF decode and idle only | animation-group dispatcher (`PlayGroup`, `PickIdle`, `IsAnimPlaying`) with text keys; locomotion/attack state machine; first-person hands; equipment masking | clip selection logs vs original groups |
| Doors and containers | passage and obstruction acceptance pending; locks, keys, traps, ownership, respawn, saved state absent | extend the container receipt with lock/key/trap/owner; persist state | desktop passage test + phone gate |
| Audio | door sounds; native audio enabled | footsteps, music selection by cell/region, attenuation curves, voice lip-sync (`.lip`) | audio event log vs expected |
| Trees | billboards only; no trunk collision, wind, 3D trunks; grass absent | measure trunk collision; implement SpeedTree branch/frond/leaf shaders per the exe's three shader families; grass from LAND/REGN data | screenshot diff |
| Scripts, quests, journal | 66% call-site coverage; 0.25 s object tick unverified; silent zero returns | coverage report in CI; subsystem-first implementation (section 6, phase 2); flag value-returning stubs loudly; budget and profile the tick | coverage percentage, MQ walkthrough |
| Dialogue and voices | topic-list rule inferred; plain list UI; no lip-sync | read `TESTopic`/`TopicInfoArray`/`DialogMenu` code; replace UI with the menu interpreter; add lip-sync | topic list per NPC vs original game |
| Touch controls and menus | BACK button works; real acceptance pending | include in device gate script (open/close each menu) | gate report |
| Crash handling | symbols kept in shipped lib | build-id + offsets in the log; symbolication script in `tools/` | crash drill |
| Probes and evidence | desktop probe runs the wrong vintage for phone claims | build probe from the phone revision; keep a second probe on master as an upgrade canary | same probe, both vintages |
| Documentation | contradictions (F5) | one machine-readable ledger generates README status, PARITY and STATUS; HANDOFF reduced to "current state, next steps, traps"; history moved to `docs/history/` | CI fails if a ledger row has no evidence link |

## 6. How to continue (phased, each phase ends with an acceptance gate)

### Phase 0: make the loop trustworthy (do first; about a week)
1. **Device gate.** Install Android `platform-tools` on the build host; the owner enables *Wireless debugging* once
   (pairing code) and keeps the phone on the tailnet. Add `tools/android/device_gate.py`:
   install, launch, run a deterministic scenario (walk 5 s, stairs, open door, talk, open and close journal and each menu
   with BACK), capture `screencap`, `logcat`, the scene log and frame-time samples, and write a pass/fail JSON. Fallback if
   `adb` is not possible: an in-app **Run acceptance script** button that executes the same scenario and uploads the
   result to the sideload server (the QA upload page exists).
2. **One engine revision.** Preferred: rebase the receipts onto a single OpenMW revision for both targets and build the
   Android library from it (measure the effort: the donor adds Android glue and GL4ES; the 8 patch pairs are small).
   Minimum: build the desktop probe from the donor revision so probes exercise shipped code. Collapse the ~30 env switches
   into one "classic" profile and test only that.
3. **CI**: `git apply --check` of every receipt against the pinned sources for both vintages; run the Lua/C++ fixtures;
   add the command-coverage report (section 4) as a non-failing metric first, then a floor.
4. **Slim updates**: stripped lib, master moved to the data payload, hot overlay channel (see table).
5. **Docs reset**: write `docs/ledger.yaml` (feature, status, evidence, oracle, last verified build); generate README
   progress, PARITY and a short STATUS from it; archive HANDOFF history; fix the contradictions in section 3, F5.
6. **Phone batch acceptance** of 0.40-0.44 with the device gate (trees, journal, conversation, voices, object scripts,
   menu exit). **Fix the build host's RAM** (or double-build and compare) before trusting more builds.
Gate: one command produces a device report for the current build; a Lua-only change reaches the phone as a small overlay.

### Phase 1: ruleset core
Build `tes4_rules` (Lua first, native where hot): the 8 attributes, 21 skills, derived health/magicka/fatigue,
encumbrance, regeneration, fatigue effects, skill use and level-up, fall damage, swimming and breath, all driven by an
**effective settings table** (master record, else executable default, plus the INI defaults file). Package-time tool:
`gmst_defaults.py` output merged with the master's GMST records into `tes4data/settings.lua` (private). Wire into
movement, jump, swim and weight first. Gate: sampler/console agreement for walk, run, sneak, jump height, fall damage,
swim speed and weight slowdown.

### Phase 2: close the script subsystems (66% to above 95% of call sites)
Implement subsystems, not commands. Order by missing sites: (1) AI packages (`PACK` evaluation, `EvaluatePackage`,
`AddScriptPackage`, alert/look), (2) magic (`SPEL`/`MGEF` effects, cast pipeline), (3) animation groups, (4) speech and
sound, (5) combat state, (6) world and object state, (7) actor values. For each: pick the executable class from the
RTTI map as the spec, read the relevant functions, write fixtures from console or sampler values, then implement.
Command stubs that return values must log loudly and be counted. Use `decomp-matching-workflow/scripts/claimq.py` to
split the 195-command backlog among workers; define the per-command acceptance (compile + fixture + one script run).
Gate: coverage report above 95%; the main quest from the prison exit through Weynon Priory and the first Kvatch scene
runs with no stubbed value-returning commands on its path.

### Phase 3: UI parity through the original menu files
Write an interpreter for `menus/*.xml`: entity expansion (`&true;`), `include`/`ref`/`copy`, arithmetic and `eq`/`onlyif`,
`user0..N`, text with `strings.xml`, images from DDS, click handlers. Render through OpenMW's Lua UI first. Per menu, a
small controller fills user traits from game state (the exe's `InventoryMenu`, `ContainerMenu`, `NegotiateMenu`,
`PersuasionMenu`, `LockPickMenu`, `LevelUpMenu`... show what each reads). Order: HUD, dialogue, journal, container,
inventory, message/quantity, barter, persuasion, level-up, lockpick, book, map. Gate: the probe renders each menu at
the original 1280x720 and matches reference captures taken under Proton (screenshot diff within a stated tolerance), and
every menu has a touch exit.

### Phase 4: actors, creatures, social systems
`Tes4Actor` component with the process LOD ladder the exe uses (high, middle-high, middle-low, low), creature bridge,
factions, crime and fame, disposition, persuasion and barter using the recovered constants, detection and sneak.
Gate: scripted encounters (bandit, scamp, guard crime) match console-measured outcomes.

### Phase 5: world completeness and performance
Exterior streaming within a measured memory budget, distant LOD (`distantlod/` holds 9,944 meshes), water, grass,
weather and time, SpeedTree shaders, interior/exterior transitions, then the renderer decision (GL4ES vs native GLES vs
Vulkan) from device-gate frame-time and thermal data. Gate: 10-minute walk through Chorrol to Weynon with logged frame
time and memory.

### Phase 6: saves, expansions, mods
A save format that captures quests, script variables, actor and inventory state first; original save compatibility is a
separate research item. Then Shivering Isles and Knights of the Nine plugins, then mod compatibility.

### Multiplayer and Vulkan
Keep deferred; the charter and ARCHITECTURE should say so. A server-authoritative core only makes sense once the ruleset
module (phase 1) exists as a clean, headless library.

## 7. Verification targets that the new recon tools make cheap
1. Topic-list construction and greeting selection: `TESTopic`, `TopicInfoArray`, `DialogMenu` (RTTI + string pivots).
2. Object-script cadence: where `Script` runs for references in loaded cells.
3. Leveled-list evaluation and say-once handling.
4. `GetInCell` and dummy-cell semantics.
5. Lip-sync and emotion channels next to the voice strings (`.lip`, seven emotion names).
6. The Tile/menu runtime: how user traits are updated per frame.
Method: RTTI class -> vtable slots -> callers, string pivot -> function, then confirm against console or sampler; record
the evidence level in the ledger.

## 8. Decisions needed from the owner
- Allow `adb` wireless debugging over Tailscale (or accept the in-app acceptance button).
- Appetite to move Android to a newer OpenMW revision (effort versus permanent savings).
- Priority between phase 2 (AI packages and magic) and phase 3 (UI parity) once phase 1 lands; recommendation: phase 2
  subsystems first for the AI/animation/magic ones, UI interpreter in parallel because it is independent.
- Replace the faulty RAM stick.
- Confirm multiplayer stays deferred.

## 9. Addendum 2026-10-06: the device loop without the phone

The owner asked to keep the phone out of testing for now, so the device gate was built on an emulator.
Fact: the shipped arm64 libraries cannot render in an x86_64 emulator (crash in the translation layer's GLES proxy,
Android 14 and 16, host GPU and software). A native x86_64 build of the same receipt-patched source works
(`tools/native/build_emulator_x86_64.sh`, `tools/android/make_emulator_apk.py`), and `tools/android/device_gate.py`
now passes six checks on an Android 16 emulator: launcher ready, engine started, 20 s stable, drawn frame, journal
opens, system BACK closes it. F1 is therefore reduced from "no device loop" to "no phone loop": Phase 0 item 1 is done
for emulators and the same script runs on a phone only with `--allow-physical`. The gate also caught a start-up
deadlock (see [ANDROID.md](ANDROID.md)) and verified the system back-key fix (`GameActivity.dispatchKeyEvent`),
both fixed in the Java host and awaiting packaging as the next phone build. Still open: phone batch acceptance of
0.40-0.44, frame-time evidence (an emulator proves nothing about phone speed), the other menus and the scripted
walk/stairs/door/talk scenario in the gate, and CI for the gate (needs a runner with KVM).

## 10. Addendum 2026-10-06 (night): the device loop is real now

Phone testing resumed the same evening. Phase 0 items that moved: the device gate runs on the real phone (6 of 6), `tools/android/phone_perf.py`
measures frame pacing, memory and threads (first result: 120 fps, no dropped frames, 1.8 GB, light scenes only; see
[PHONE_PERF_20261006.md](research/PHONE_PERF_20261006.md)), wireless adb removes the cable-drop problem, and the engine can log a quantity on the
device (the jump line) so a desktop-invisible bug was found in minutes. The biggest open risk is still performance in dense scenes (Imperial City,
forests, crowds) and at native resolution; the launcher cannot start there yet. The original controller's laws are now recovered and checked by
replaying its own logged steps ([TES4_AIRBORNE.md](research/TES4_AIRBORNE.md)); the owner's feel rule ("always like the original; liberties only
for touch") is in AGENTS.md and the deviation ledger in PARITY.md.
