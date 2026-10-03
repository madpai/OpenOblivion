# TES4 interaction checkpoint, 2026-10-03

The interrupted work added container Lua scripts and declared native NPC,
creature and container bindings without implementing them. The completed
checkpoint supplies name/base-inventory snapshots, typed cell queries,
shared-skeleton part attachment and GUI touch forwarding. Source application
is reproducible against the exact desktop and Android pins through
`tools/native/tes4_interactions.py`; unknown inputs are rejected before writes.

## Native results

The private Vilverin scene resolves five NPC display names, including the
ringleader, and enumerates fourteen containers with thirty-three base inventory
rows. These rows are direct CNTO entries. Leveled lists are not rolled and
unnamed entries remain labeled unresolved. No item is transferred or created
by opening this inspection window.

The stock Reference loader does not reset optional lock fields before reuse.
Initially all fourteen containers appeared locked. An independent local
master walk found XLOC on only three. Resetting lock state, level and key at
the start of each load produces eleven unlocked containers and preserves
the three authored locks. The original synthetic unlocked/locked/unlocked
fixture uses the unchanged upstream reader and the same original reset helper.
The founding read-only inspector and its immutable source cache stay unchanged.

NPC scene roots report seventy mapped skeleton nodes before equipment/parts
are inserted. Parts are attached through OpenMW's existing skinned-geometry
attachment path so their private skeletons do not shadow the actor skeleton.
This is scene assembly evidence. It does not demonstrate original KF playback,
equipment-slot coverage, facial animation or first-person hands. Actors remain
in a bind pose; the complete skin/bone coverage audit remains required.

## UI and device scope

The global activation handler rejects locked/trapped objects and non-player
activators. A player event displays the container's base entries in a bounded
window. The interface pauses simulation, shows the native cursor and closes
through its Close row or the engine's interface exit. The phone overlay sends
absolute GUI taps while the cursor is shown and releases held controls when
switching between GUI and world input. World controls resume afterwards.

The private desktop probe passes record lookup, activation, visible window
capture, close/resume and clean scene exit. The captured window was inspected.
It shows a sack with an unresolved leveled entry; this is explicitly a base
inventory inspection, not completed loot gameplay. Desktop and Android native
builds pass. No physical device is connected to ADB, so physical-phone touch
and rendering acceptance remains pending owner QA.

The inherited door script probes an optional sequence function before using
the existing hide/toggle fallback. The native engine does not yet provide
embedded TES4 door sequence playback; that work is still open. Controller
manager/multi-target controller diagnostics identify the remaining path.

## Evidence and continuation

Public validation comprises thirteen CTest groups and the publication guard.
Private evidence lives under `openoblivion-private/evidence`:
`grok-handoff-20261003` (source backup, build receipts, master lock scan and
native/public builds) and `tes4-interactions-desktop-12f` (passing scene probe,
logs and inspected captures). Earlier failed probes remain available.
Raw game content and captures are not added to GitHub.

Next: resolve original controller sequences and KF tracks, implement
per-reference leveled inventory/transfer/equipment with durable state, and
continue the motor/gameplay/script parity gates in [PARITY.md](../PARITY.md).
The 0.5 stair filter and current body/step constants remain unchanged.
