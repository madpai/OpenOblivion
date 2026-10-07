# First phone frame-pacing and memory measurements

Date: 2026-10-06. Build `0.44-menu-exit` (the served phone build), installed on the owner's Galaxy S24+ (SM-S926U, 12 GB, Android 16)
and driven over USB with `tools/android/device_gate.py` and measured with `tools/android/phone_perf.py`. The owner resumed phone
testing the same day and plugged the phone in. Raw output stays in the private workspace
(`evidence/phone-perf/`); screenshots show game content and are never committed.

## What was measured, and how

`phone_perf.py` is read-only. Frame pacing comes from SurfaceFlinger's per-layer time statistics for the game's SurfaceView layer
(Android 16 no longer returns per-frame timestamps from `--latency`): frames presented, dropped frames and the present-to-present
histogram. It also records process memory (`dumpsys meminfo`), the busiest threads (`top -H`) and battery/thermal state.

Phone state: display set to **720 x 1560** (HD+) at up to 120 Hz, battery 61%, charging over USB, 232 GB free, thermal status 0
throughout, about 3 GB of the 12 GB free (other apps resident).

## Results (0.44, three runs in two scenes)

| Scene | Seconds | Frames presented | Dropped | Present interval p99 | Engine thread | Memory (PSS) | Battery temp |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sewer-exit spawn, idle | 15 | 1,801 | 0 | 8 ms | 81% of one core | 1.88 GB | 31.0 to 33.6 C |
| Sewer-exit spawn, move pad held forward (player swam to the shore) | 26 | 3,119 | 0 | 8 ms | 89% | 1.88 GB | 34.8 C |
| "Vilverin Exterior" start, idle | 20 | 2,397 | 0 | 8 ms | 77% | 1.82 GB | 36.3 C |

Every present interval was 8 ms: the scenes ran at the display's 120 Hz with no dropped frames, no frame over 33 ms and no thermal
throttling. The gate also passes on the phone (launcher, scene start, 15 s stable, a drawn frame, journal open and close).

## What this does and does not say

- **It says** the engine can present a light scene at 120 frames per second on this phone at 720p with the single-threaded OSG
  setting, using most of one big core, 1.8 GB of memory and little heat.
- **It does not say** the game will hold that in the places that matter. Both scenes are sparse: a lake edge with distant ruins and a
  foggy shoreline. The Imperial City, forests with many trees, interiors with several actors and combat are untested, and the
  launcher offers no way to start there yet. The engine thread already sits at 77 to 89% of a core for these light scenes while the
  display caps frames at 120, so headroom to the 60 fps budget is roughly 2 to 3 times at most, not tens of times.
- **Resolution matters.** The phone renders at 720 x 1560. Native 1080 x 2340 costs more fill rate; this was not tried.
- Memory use is stable (no growth over 26 s of movement because no new cells streamed). Streaming a large world is untested.

## Next measurements

1. A dense scene: start inside or beside the Imperial City and in a forest (needs a start-position option or an overlay teleport),
   with NPCs, then repeat idle and walking runs.
2. Native display resolution and the real touch-play session length (10 minutes or more) for thermal behaviour.
3. Frame-time percentiles from inside the engine for cell loads, which SurfaceFlinger's histogram smooths over.
4. Build `0.45-airborne` on the phone (the original jump and gravity); phone feel is the owner's test.

## Notes

- `device_gate.py` leaves the app on its launcher screen (its last BACK press); start the scene again before sampling.
- On this phone the gate's system-BACK check passed on 0.44, although the earlier session recorded that the system BACK key did not
  close the journal. The discrepancy is unexplained; do not treat the Java fix as proven necessary or sufficient.
- Touch coordinates for `input` are in the display's landscape space (1560 x 720 here), not the panel's native portrait size.
