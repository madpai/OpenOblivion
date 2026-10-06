#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Scripted Android device gate: launch the preview, start the scene, open and close the journal.

It drives one adb device and writes gate-result.json plus screenshots and logcat into an evidence
folder outside the checkout (they show the owner's game content; never commit them). Checks:

  launcher_ready    the launcher reports the installed assets as ready
  scene_started     the engine thread starts (SDL_main) and the game window gets focus
  scene_stable      the scene process stays alive with no native or Java crash for --hold seconds
  scene_renders     a screenshot shows a drawn frame (not blank or flat)
  journal_opens     MORE then JOURNAL shows the journal (the overlay's BACK button appears)
  back_key_closes   the system BACK key closes the journal again

The serial is required. Only emulators (emulator-NNNN) are accepted unless --allow-physical is given,
so a script run never reaches the owner's phone by accident. Screen positions are fractions of the
landscape screen, calibrated on a 20:9 display (2400x1080); the overlay's own layout decides them.
"""
import argparse
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

PACKAGE = 'org.openoblivion.preview'
SCENE_PROCESS = PACKAGE + ':scene'
CRASH = re.compile(r'Fatal signal|FATAL EXCEPTION|ANR in ' + re.escape(PACKAGE))
# (x, y) as fractions of the landscape screen
MORE = (0.972, 0.457)
JOURNAL = (0.924, 0.565)
# the overlay BACK button's box while a menu is open: (x0, y0, x1, y1) fractions; black letterbox otherwise
BACK_BOX = (0.92, 0.08, 0.99, 0.15)


class Device:
    def __init__(self, serial, adb):
        self.serial, self.adb = serial, adb

    def run(self, *args, check=True, timeout=120, binary=False):
        out = subprocess.run([self.adb, '-s', self.serial, *args], capture_output=True, timeout=timeout, check=False)
        if check and out.returncode != 0:
            raise RuntimeError('adb %s failed: %s' % (' '.join(args), out.stderr.decode(errors='replace').strip()))
        return out.stdout if binary else out.stdout.decode(errors='replace')

    def shell(self, command, **kw):
        return self.run('shell', command, **kw)

    def screenshot(self, path):
        data = self.run('exec-out', 'screencap', '-p', binary=True)
        Path(path).write_bytes(data)
        from PIL import Image
        return Image.open(path).convert('RGB')

    def tap_fraction(self, image, point):
        x, y = int(point[0] * image.width), int(point[1] * image.height)
        self.shell('input tap %d %d' % (x, y))

    def ui_nodes(self):
        self.shell('uiautomator dump /sdcard/gate_ui.xml', check=False)
        xml = self.shell('cat /sdcard/gate_ui.xml', check=False)
        try:
            root = ET.fromstring(xml[xml.index('<'):])
        except (ValueError, ET.ParseError):
            return []
        nodes = []
        for node in root.iter('node'):
            m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', node.get('bounds', ''))
            if m:
                x0, y0, x1, y1 = map(int, m.groups())
                nodes.append((node.get('text', ''), ((x0 + x1) // 2, (y0 + y1) // 2)))
        return nodes

    def tap_text(self, text, contains=False):
        for label, (x, y) in self.ui_nodes():
            if label == text or (contains and text in label):
                self.shell('input tap %d %d' % (x, y))
                return True
        return False

    def focus(self):
        for line in self.shell('dumpsys window', check=False).splitlines():
            if 'mCurrentFocus' in line:
                return line.strip()
        return ''

    def pid(self, process):
        return self.shell('pidof ' + process, check=False).strip().split(' ')[0]


def region_luma(image, box):
    import numpy as np
    w, h = image.size
    x0, y0, x1, y1 = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
    return float(np.asarray(image.crop((x0, y0, x1, y1)).convert('L')).mean())


def frame_is_drawn(image):
    import numpy as np
    pixels = np.asarray(image.convert('L'), dtype='float32')
    return bool(pixels.std() > 12.0 and (pixels > 25).mean() > 0.2)


class Gate:
    def __init__(self, device, out):
        self.device, self.out, self.checks = device, out, []

    def check(self, name, passed, detail=''):
        self.checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
        print(('PASS ' if passed else 'FAIL ') + name + (' - ' + detail if detail else ''), flush=True)
        return passed

    def crashes(self):
        log = self.device.run('logcat', '-d', check=False, timeout=60)
        return [line for line in log.splitlines() if CRASH.search(line)]

    def wait_launcher_ready(self, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            nodes = self.device.ui_nodes()
            labels = ' | '.join(text for text, _ in nodes if text)
            if any(text == 'Got it' for text, _ in nodes):
                self.device.tap_text('Got it')  # Android's one-time full-screen notice
            elif 'assets ready' in labels.lower():
                return True
            time.sleep(5)
        return False

    def run(self, apk, hold, uninstall_first, launcher_timeout):
        d = self.device
        info = {k: d.shell('getprop ' + p).strip() for k, p in [
            ('model', 'ro.product.model'), ('android', 'ro.build.version.release'),
            ('sdk', 'ro.build.version.sdk'), ('abis', 'ro.product.cpu.abilist')]}
        if apk:
            if uninstall_first:
                d.run('uninstall', PACKAGE, check=False)
            result = d.run('install', '-r', '-g', str(apk), check=False, timeout=900)
            self.check('install', 'Success' in result, result.strip().splitlines()[-1] if result.strip() else '')
        package = d.shell('dumpsys package ' + PACKAGE, check=False)
        info['version'] = (re.search(r'versionName=(\S+)', package) or [None, ''])[1]
        info['primary_abi'] = (re.search(r'primaryCpuAbi=(\S+)', package) or [None, ''])[1]
        print('device:', json.dumps(info), flush=True)
        d.shell('am force-stop ' + PACKAGE)
        d.run('logcat', '-c')
        d.shell('am start -n %s/ui.activity.MainActivity' % PACKAGE)
        ready = self.wait_launcher_ready(launcher_timeout)
        d.screenshot(self.out / '1-launcher.png')
        if not self.check('launcher_ready', ready):
            return info
        d.tap_text('Begin Journey', contains=True)
        started = False
        for _ in range(60):
            time.sleep(2)
            if 'GameActivity' in d.focus() and d.pid(SCENE_PROCESS) and 'SDL_main' in d.run('logcat', '-d', check=False, timeout=60):
                started = True
                break
        self.check('scene_started', started, d.focus())
        if not started:
            return info
        time.sleep(hold)
        crashes = self.crashes()
        alive = bool(d.pid(SCENE_PROCESS))
        self.check('scene_stable', alive and not crashes, '; '.join(crashes[:2]) or ('process alive %ds' % hold))
        frame = d.screenshot(self.out / '2-scene.png')
        self.check('scene_renders', frame_is_drawn(frame))
        top = d.shell('top -b -n 1 -p %s' % d.pid(SCENE_PROCESS), check=False).strip().splitlines()
        info['scene_top'] = top[-1].strip() if top else ''
        before = region_luma(frame, BACK_BOX)
        d.tap_fraction(frame, MORE)
        time.sleep(2)
        d.tap_fraction(frame, JOURNAL)
        time.sleep(3)
        opened = d.screenshot(self.out / '3-journal.png')
        luma_open = region_luma(opened, BACK_BOX)
        self.check('journal_opens', luma_open > before + 15, 'overlay BACK region luma %.1f -> %.1f' % (before, luma_open))
        d.shell('input keyevent KEYCODE_BACK')
        time.sleep(3)
        closed = d.screenshot(self.out / '4-after-back.png')
        luma_closed = region_luma(closed, BACK_BOX)
        self.check('back_key_closes', luma_closed < luma_open - 15, 'overlay BACK region luma %.1f -> %.1f' % (luma_open, luma_closed))
        (self.out / 'logcat.txt').write_text(d.run('logcat', '-d', check=False, timeout=120))
        return info


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--serial', required=True, help='adb serial, e.g. emulator-5582')
    parser.add_argument('--apk', type=Path, help='install this APK first')
    parser.add_argument('--uninstall-first', action='store_true', help='with --apk: remove the app (and its data) before installing')
    parser.add_argument('--hold', type=int, default=20, help='seconds the scene must stay alive before the screenshot')
    parser.add_argument('--launcher-timeout', type=int, default=600)
    parser.add_argument('--out', type=Path, help='evidence folder (default ~/openoblivion-private/evidence/gate-<time>)')
    parser.add_argument('--adb', default='adb')
    parser.add_argument('--allow-physical', action='store_true', help='permit a non-emulator serial (the owner must have asked)')
    args = parser.parse_args()
    if not re.fullmatch(r'emulator-\d+', args.serial) and not args.allow_physical:
        parser.error('refusing non-emulator serial %r (use --allow-physical only when the owner asked for a phone run)' % args.serial)
    listed = subprocess.run([args.adb, 'devices'], capture_output=True, text=True).stdout
    if not re.search(r'^%s\s+device$' % re.escape(args.serial), listed, re.M):
        parser.error('%s is not an online adb device:\n%s' % (args.serial, listed))
    out = args.out or Path.home() / 'openoblivion-private/evidence' / ('gate-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    out.mkdir(parents=True, exist_ok=True)
    gate = Gate(Device(args.serial, args.adb), out)
    try:
        info = gate.run(args.apk, args.hold, args.uninstall_first, args.launcher_timeout)
    except Exception as error:  # a broken adb call is a failed gate, with the reason recorded
        gate.check('gate_error', False, repr(error))
        info = {}
    passed = bool(gate.checks) and all(c['passed'] for c in gate.checks)
    (out / 'gate-result.json').write_text(json.dumps({'passed': passed, 'device': info, 'checks': gate.checks,
        'finished': datetime.now().isoformat(timespec='seconds')}, indent=2) + '\n')
    print('GATE ' + ('PASSED' if passed else 'FAILED') + ' - evidence in ' + str(out))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
