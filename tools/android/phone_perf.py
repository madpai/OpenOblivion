#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Read-only performance sample of a running Android app over adb: frame pacing, memory, CPU threads, temperature.

It changes nothing on the device and writes only a JSON file (default under ~/openoblivion-private/evidence/, outside the
checkout). Frame pacing comes from SurfaceFlinger's per-layer time statistics (the app's SurfaceView layer): frames presented,
dropped frames and the present-to-present histogram, so it measures what reached the screen, not what the engine thinks
it drew. (Android 16 no longer returns per-frame timestamps from `--latency`.) An emulator proves nothing about speed: use a phone.

  phone_perf.py --serial R5CX13GTDRJ --seconds 30 --label walk-exterior

Start the scene first (the device gate does this); this tool only observes.
"""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path

NO_FRAME = 9223372036854775807


def adb(serial, *args, timeout=30):
    return subprocess.run(['adb', '-s', serial, *args], capture_output=True, text=True, timeout=timeout).stdout


def find_layer(serial, package):
    """Layer names look like `RequestedLayerState{hex <name>#id parentId=...}` on Android 15+ and plain names before."""
    names = []
    for line in adb(serial, 'shell', 'dumpsys', 'SurfaceFlinger', '--list').splitlines():
        m = re.search(r'RequestedLayerState\{\w+ (.+?#\d+)', line)
        name = (m.group(1) if m else line.strip())
        if package in name and 'ActivityRecord' not in name and 'InputSink' not in name:
            names.append(name)
    game = [n for n in names if 'GameActivity' in n]
    surface = [n for n in names if 'SurfaceView' in n and not n.startswith('Background')]
    blast = [n for n in surface if 'BLAST' in n]   # the layer that actually receives the app's buffers
    ranked = blast or surface or game or names
    if not ranked:
        raise SystemExit('No SurfaceFlinger layer for %s: is the scene running and in the foreground?' % package)
    return ranked[0]


def timestats(serial, layer):
    """Enable and clear SurfaceFlinger time stats, return a function that dumps this layer's statistics."""
    adb(serial, 'shell', 'dumpsys', 'SurfaceFlinger', '--timestats', '-enable', '-clear')

    def dump():
        text = adb(serial, 'shell', 'dumpsys', 'SurfaceFlinger', '--timestats', '-dump', '-clear', timeout=60)
        for block in text.split('layerName = ')[1:]:
            if block.split('\n', 1)[0].endswith(layer.split(' ', 1)[-1]) or layer in block.split('\n', 1)[0]:
                return block
        return ''
    return dump


def histogram(block, name):
    m = re.search(name + r' histogram is as below:\n([^\n]*)', block)
    return [(int(a), int(b)) for a, b in re.findall(r'(\d+)ms=(\d+)', m.group(1))] if m else []


def hist_percentile(hist, p):
    total = sum(c for _, c in hist)
    if not total:
        return None
    running = 0
    for ms, count in hist:
        running += count
        if running >= p / 100 * total:
            return ms
    return hist[-1][0]


def pid_of(serial, package):
    out = adb(serial, 'shell', 'ps', '-A', '-o', 'PID,NAME').splitlines()
    pids = {l.split(None, 1)[1].strip(): int(l.split()[0]) for l in out[1:] if len(l.split(None, 1)) == 2}
    for name in (package + ':scene', package):
        if name in pids:
            return name, pids[name]
    return None, None


def meminfo(serial, name):
    text = adb(serial, 'shell', 'dumpsys', 'meminfo', name)
    out = {}
    for key, pattern in (('total_pss_kb', r'TOTAL PSS:\s+(\d+)'), ('native_heap_kb', r'Native Heap:?\s+(\d+)'),
                         ('graphics_kb', r'Graphics:\s+(\d+)'), ('rss_kb', r'TOTAL RSS:\s+(\d+)')):
        m = re.search(pattern, text)
        if m:
            out[key] = int(m.group(1))
    return out


def threads(serial, pid):
    rows = []
    for line in adb(serial, 'shell', 'top', '-b', '-n', '1', '-H', '-p', str(pid)).splitlines():
        parts = line.split()
        if len(parts) >= 12 and parts[0].isdigit():
            try:
                rows.append({'tid': int(parts[0]), 'cpu_percent': float(parts[8].replace('%', '')), 'name': ' '.join(parts[11:])})
            except ValueError:
                pass
    return sorted(rows, key=lambda r: -r['cpu_percent'])[:6]


def thermal(serial):
    battery = adb(serial, 'shell', 'dumpsys', 'battery')
    temp = re.search(r'temperature:\s*(\d+)', battery)
    status = re.search(r'Thermal Status:\s*(\d+)', adb(serial, 'shell', 'dumpsys', 'thermalservice'))
    return {'battery_temp_c': int(temp.group(1)) / 10 if temp else None, 'thermal_status': int(status.group(1)) if status else None}


def percentile(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, int(p / 100 * len(values)))]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--package', default='org.openoblivion.preview')
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--label', default='sample')
    parser.add_argument('--out', type=Path, default=Path.home() / 'openoblivion-private/evidence/phone-perf')
    args = parser.parse_args()
    name, pid = pid_of(args.serial, args.package)
    if not pid:
        raise SystemExit('%s is not running' % args.package)
    layer = find_layer(args.serial, args.package)
    result = {'label': args.label, 'serial_tail': args.serial[-4:], 'process': name, 'layer': layer, 'start': thermal(args.serial),
              'memory_start': meminfo(args.serial, name)}
    dump = timestats(args.serial, layer)
    time.sleep(args.seconds)
    block = dump()
    result['cpu_threads'] = threads(args.serial, pid)
    result['memory_end'] = meminfo(args.serial, name)
    result['end'] = thermal(args.serial)
    stats = {}
    for key in ('totalFrames', 'droppedFrames', 'lateAcquireFrames', 'jankyFrames', 'averageFPS'):
        m = re.search(key + r' = ([\d.]+)', block)
        if m:
            stats[key] = float(m.group(1))
    hist = histogram(block, 'present2present')
    stats.update({'present_interval_p50_ms': hist_percentile(hist, 50), 'present_interval_p95_ms': hist_percentile(hist, 95),
                  'present_interval_p99_ms': hist_percentile(hist, 99), 'present_intervals_over_33ms': sum(c for ms, c in hist if ms > 33),
                  'present_intervals_over_100ms': sum(c for ms, c in hist if ms > 100)})
    result['frames'] = stats
    result['seconds'] = round(args.seconds, 1)
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / ('%s-%s.json' % (time.strftime('%Y%m%dT%H%M%S'), args.label))
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('layer', 'cpu_threads')}, indent=1))
    print('top threads:', [(t['name'].split()[0], t['cpu_percent']) for t in result['cpu_threads'][:4]])
    print('written', path)


if __name__ == '__main__':
    main()
