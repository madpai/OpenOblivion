# Format and behavior research

The first target is classic Oblivion (2006), not Remastered. Every supported
version/feature must have an original fixture and a private real-content check.

| Boundary | Confirmed now | Unresolved work / evidence needed |
|---|---|---|
| TES4 ESM/ESP container | Original 20-byte record/group headers, 1.0/1.2 HEDR, nested groups and compressed-record scanning reproduced through unchanged OpenMW code. Owner master scan passed. | Load-order/master mapping, overridden/deleted records, dependency resolution and typed gameplay semantics. |
| Form identity | OpenMW contains FormId/mod-index facilities; the foundation scanner does not resolve an installation's load order. | Use plugin identity + source local ID for stable persistence; remap all master references. Never persist a transient top-byte index as the sole identity. |
| BSA | Existing Asset Lab v103 tests pass; one real static NIF member matches upstream extraction byte-for-byte (11,661 bytes). Upstream viewer mounts owner base archives. | Loose-file/archive precedence, case handling, load order and broader archive/member coverage. |
| NIF | Asset Lab static tests pass. One real static model passes upstream niftest; interior/exterior textured geometry rendered by unchanged OpenMW. | Skin/bind transforms, equipment, KF/controllers, particles, alpha/shaders and collision shapes. Logs report unsupported interpolators and some missing textures; do not assume full decoding implies full runtime behavior. |
| DDS | No OpenOblivion decode/render implementation is established. | Reuse existing texture handling; inspect color space, normal maps, mip chains, compression and Android GPU format support. |
| KF animation | No original KF animation proven here. | Correlate NIF skeletons, node names, text keys, interpolation and locomotion events. Frozen pose/root animation is not KF compatibility. |
| Physics | No Havok binary dependency. Bullet core is a candidate; OpenMW collision code is a reference. | Translate supported collision shapes, units and controller behavior; reject/report unsupported shapes and measure gameplay differences. |
| Compiled scripts / conditions | xEdit TES4 definitions and xOBSE command knowledge are research references. | Classic SCPT/SCDA and conditions require explicit VM semantics and event ordering. These are not Skyrim PEX or automatically translatable server Lua. |
| Quests/dialogue | Record structure references exist; no quest runtime implemented. | Separate actor/player-local progress from world/party state; identify single-player script assumptions and authorized effects. |
| Audio/UI | No OpenOblivion audio or UI implementation. | Owner-supplied audio paths/codec support; original touch UI, font licensing and accessible HUDs. |

## Investigation method

Measure coordinates, handedness, units, scale, winding, pivots, bone spaces,
alpha and attachment/grip positions on a small representative slice. Record
source hashes privately, parser version, unsupported features and authored
conversions. Compare meaningful decoded values between existing readers before
normalizing. Verify native rendering/collision/equipment after loading.

Keep original file paths and loss diagnostics in private reports. Public
fixtures use independently authored values and shapes. Raw output remains
private; reviewed counts or failure descriptions can enter public evidence.
Successful parsing never implies an asset has distribution rights.

## Known upstream behavior

At pinned OpenMW revision `46bd4599203ee52ffc0f3e8edb3fc159a0303a49`,
`ReaderUtils::readItem` checks `hasMoreRecs()` after `getRecordHeader()`.
The latter advances the file-read counter across the current grouped record's
body, so the final record can be omitted. Original one-record group fixtures
reproduce this. Our independently authored iteration checks for the next header
before reading it, then processes that header even at the last record.

The upstream reader skips `XXXX` extended subrecord payloads. Reported
subrecord counts represent the reader's visited subrecords, not all semantic
fields. Container checks bound file/record/group sizes and decompression
allocation declarations, but do not validate every payload or isolate the
parser process. Trusted owner files are the current input scope.
