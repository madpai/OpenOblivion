# Multiplayer and persistence contract

Status: design requirements for the first cooperative implementation. No
networking/server/persistence code exists yet.

## Authority

| State/action | Client responsibility | Server responsibility |
|---|---|---|
| Movement | Send sequenced input; predict local presentation | Simulate collision, enforce speed and reconcile |
| Attack/cast | Request action with target/aim/time context | Check life state, cooldown, reach/resources, hit and effects |
| Enemy AI | Present replicated state | Own decision making, targets, health, death and loot |
| Inventory/equip/trade | Send intent with revision/expected object | Validate ownership, capacity and one committed transfer |
| XP/skills/gold | Display authoritative results | Compute awards from accepted events; never accept client totals |
| Death/respawn | Show death state; request allowed respawn | Commit one death transition, apply policy, choose spawn and restore resources |
| Quests/world changes | Request interaction | Scope state to player/party/world/instance and validate consequences |
| Save/reconnect | Resume authenticated identity | Load durable committed state and issue an authoritative baseline |

Solo runs use a local authority. Player death does not force a save reload in
cooperative modes. Classic mode may select different death/save behavior.

## First protocol slice

Define a versioned handshake with content/rules manifests before creating the
player. Commands carry session epoch, monotonically increasing sequence,
actor identity and bounded payload. The authenticated connection determines
the actor; a payload cannot choose another player. Duplicate/stale commands
cannot issue another attack or award. Test finite numbers, oversize/truncated
packets, wrong identities and impossible interactions.

Use an existing transport: ENet is the initial candidate, subject to a real
Linux/NDK build and dependency audit. Reliable events carry inventory/death/
rewards; transient snapshots carry positions and animation state. Reliability
does not provide authentication or encryption. The first test binds loopback;
an authenticated protected transport/tunnel and reconnect model must be
defined before an Internet-facing service is enabled. No automatic public
listener is part of the founding tools.

The server chooses one logical simulation time and orders accepted actions.
Tick rates, snapshot rates, entity limits and interpolation windows are
authored tuning to measure in the first slice, not recovered Oblivion facts.
Interest follows cells/instances and nearby relevant actors; entering interest
receives a baseline plus ordered subsequent events. Joining clients cannot
claim authority over unowned NPCs.

## Durable state

SQLite is the first persistence candidate, with one simulation owner and a
bounded persistence queue. Store account/character identity separately from
world/instance identity. Schema version and content/rules digest accompany
state; migrations preserve ownership/progression or refuse incompatible saves.
Credentials/tokens and owner databases remain private.

A reward has a stable event ID. Record its acceptance and all gold/XP/item
changes in one transaction before acknowledging the durable outcome. Replay
of the same event must return its existing result. A death records transition,
penalty and respawn eligibility atomically; reward, corpse and spawn creation
use stable IDs. If persistence fails, fail the operation visibly and prevent
uncommitted rewards from being spent. Do not claim exactly-once delivery;
implement idempotent committed effects.

Acceptance tests cut the server process before/after commit and acknowledgement,
then restart/reconnect. Verify no duplicated loot/XP, no lost acknowledged
progress, no dead player permanently stuck and no cross-instance state leaks.
Add backup/restore and schema migration checks before a persistent public mode.

## Mode policy

| Mode | Death and start | State lifetime | Compatibility approach |
|---|---|---|---|
| Cooperative dungeon | Authored alternate start; checkpoint respawn | Character persists, dungeon resets by server policy | Small supported combat/loot slice; quests opt in |
| Arena / Gatebound-like PvE | Wave entry; bounded respawn/penalty options | Persistent progression, bounded encounter state | Original server rosters and rewards with owner-supplied visuals |
| Persistent Cyrodiil | Server-selected starts/checkpoints | Explicit world/party/player state, scheduled resets | Expand only after streaming and script authority are proven |
| Classic offline | Original/classic start and configurable death/save rules | Local world and character | Reuse compatibility VM and faithful semantics as coverage grows |

Lua scripts receive events and validated engine operations with time/memory
limits and deterministic authority ordering. No filesystem/process/network
access by default. Select dependencies and sandbox semantics when the first
mode needs them; no fake Lua API is advertised now.

