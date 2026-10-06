# Executable recon (Oblivion.exe)

Date: 2026-10-06. Static analysis of the owner's retail Steam `Oblivion.exe` (x86, MSVC, fixed image base, no base
relocations, wrapped by a protection stub whose entry point sits in a high-entropy section; the code and data sections
are readable and are all that was used). Tools are the generic scripts in the public
[game-decomp-compendium](https://github.com/madpai/game-decomp-compendium) (`re-binary-recon`, `bethesda-gamebryo-re`).
Nothing here is copied from the executable: only the method, counts and rules are recorded. Dumps (class map, setting
defaults) are generated locally into `~/openoblivion-private/research/` and never committed. Evidence levels: *static*
(read from the binary) and *verified* (second source or measured on data).

## Findings

| Finding | Evidence | Why it matters |
|---|---|---|
| The executable carries full MSVC RTTI: 1,715 vtables for 1,482 distinct classes (TESForm hierarchy, the whole Ni* scene graph, Havok wrappers, SpeedTree shader classes, ~38 menu classes), recoverable in 0.15 s | static | Names for engine behaviour without debug info; anchors for string pivots and virtual-slot reading |
| Voice files are `<quest>_<topic>_<INFO id, 8 hex digits>_<response number>` under `Data\Sound\Voice`; game type `mp3`, source `wav`, lip-sync `lip` | **verified**: executable format string, archive contents, and the bsa-rs documentation example | Confirms the naming used by the conversation window; shows lip-sync files exist (not used yet) |
| The command table is a data table of 40-byte records referenced from data, not code | static, consistent with the extractor | Explains why name pivots find no code references |
| ~2,050 game settings (GMST) have built-in defaults compiled into static initializers; the plugin's GMST records override them | static; the extraction covers 378 of the 382 GMST records in Oblivion.esm by name | A setting absent from the master is not absent from the game: its effective value is the exe default |
| Condition (CTDA) records are 24 bytes in all 48,531 conditions of the master's INFO records | **verified** on data | The dialogue engine's layout assumption holds for the whole master |

## Consequences for the port
1. **Movement settings**: the HANDOFF notes several movement settings absent from the master. Their effective values come from
   the executable's defaults; regenerate the table locally with
   `python3 skills/bethesda-gamebryo-re/scripts/gmst_defaults.py Oblivion.exe --esm Oblivion.esm` (compendium repository)
   and apply "plugin value if present, else exe default" in the game-settings loader instead of inventing values. Character body
   dimensions are not GMSTs (Havok character proxy) and remain unrecovered.
2. **Conversation window**: topic list, greeting selection and quest-script delay can now be checked against the code of
   `TESTopic`, `TESTopicInfo`, `TopicInfoArray`, `DialogMenu` and `TESQuest` instead of inferred; see the status table in
   [TES4_SCRIPTS.md](TES4_SCRIPTS.md).
3. **Lip-sync and expressions**: `.lip` files and seven emotion names sit next to the voice strings, so facial animation
   data exists; barter (`NegotiateMenu`), persuasion, lockpicking, alchemy, enchantment, level-up and race/sex menus exist
   as classes and form a menu roadmap.
4. **Trees**: three SpeedTree shader families (leaf, frond, branch) with lighting properties define the original look; the
   billboard approximation can be compared against them.

## Method (reproducible)
`pe_info.py` (build id, relocations, sections) -> `rtti_scan.py` (class map) -> `string_xrefs.py --grep` (string to
function) -> `gmst_defaults.py` (setting defaults). Each script is read-only and dependency-free. Record the PE timestamp
with any result; do not apply addresses to another build.
