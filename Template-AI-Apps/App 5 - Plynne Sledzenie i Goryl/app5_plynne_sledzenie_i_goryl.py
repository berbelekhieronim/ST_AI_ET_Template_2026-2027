#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APP 5: PLYNNE SLEDZENIE I GORYL (Smooth pursuit + saccades + "gorilla")
=======================================================================
Flow:
  1. 5-point Tobii calibration
  2. 15 s: ball moving along an infinity shape (smooth pursuit)
  3. 10 s: ball popping in/out in the UPPER-LEFT quadrant (saccades)
     while a subtle infinity-moving "gorilla" ball runs in the LOWER-RIGHT quadrant
  4. Question: did you notice anything else?
  5. Results: scanpaths, basic metrics, was the gorilla seen (gaze + self-report)

Without a tracker the app falls back to the mouse (simulated gaze) for testing.
ESC quits at any time.
"""

import csv
import math
import random
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================================================
# 0. TOBII SDK SETUP
# ============================================================================
HERE = Path(__file__).resolve().parent
SDK_PATH = HERE.parent / "x3-120 SDK" / "64"
if SDK_PATH.exists():
    sdk_str = str(SDK_PATH)
    if sdk_str not in sys.path:
        sys.path.append(sdk_str)

# ============================================================================
# 1. IMPORTS
# ============================================================================
from psychopy import core, event, logging, visual

logging.console.setLevel(logging.ERROR)

try:
    import tobii_research as tr
    TOBII_OK = True
except Exception:
    tr = None
    TOBII_OK = False

# ============================================================================
# 2. CONSTANTS
# ============================================================================
FULLSCREEN = True

PURSUIT_SECONDS = 15.0
SACCADE_SECONDS = 10.0

PURSUIT_PERIOD = 5.0        # one infinity loop (s) -> 3 loops in 15 s
PURSUIT_AMP_X = 0.36        # fraction of screen width
PURSUIT_AMP_Y = 0.20        # fraction of screen height
BALL_RADIUS = 18

TARGET_ON = 0.6             # saccade target visible (s)
TARGET_OFF = 0.4            # blank between targets (s)
TARGET_MIN_JUMP = 250       # min distance between consecutive targets (px)
TARGET_HIT_RADIUS = 150     # gaze within this distance counts as "reached target"

GORILLA_PERIOD = 4.0
GORILLA_AMP_X = 0.07
GORILLA_AMP_Y = 0.055
GORILLA_RADIUS = 5
GORILLA_COLOR = [-0.80, -0.80, -0.80]   # barely lighter than the black background
GORILLA_MARGIN = 90                     # px around the path counted as "looking at gorilla"
GORILLA_SEEN_DWELL = 0.25               # s of cumulative gaze dwell to count as seen

SACCADE_VELOCITY = 1000.0   # px/s threshold for saccade detection

CAL_POINTS = [(0.5, 0.5), (0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]


# ============================================================================
# 3. GEOMETRY
# ============================================================================
class Screen:
    W = 1920.0
    H = 1080.0

    @classmethod
    def update(cls, win):
        w, h = win.size
        cls.W, cls.H = float(w), float(h)


def norm_to_pix(nx, ny):
    return (nx - 0.5) * Screen.W, (0.5 - ny) * Screen.H


def pursuit_pos(t):
    w = 2.0 * math.pi / PURSUIT_PERIOD
    return (
        PURSUIT_AMP_X * Screen.W * math.sin(w * t),
        PURSUIT_AMP_Y * Screen.H * math.sin(2.0 * w * t),
    )


def gorilla_center():
    return 0.25 * Screen.W, -0.25 * Screen.H


def gorilla_pos(t):
    cx, cy = gorilla_center()
    w = 2.0 * math.pi / GORILLA_PERIOD
    return (
        cx + GORILLA_AMP_X * Screen.W * math.sin(w * t),
        cy + GORILLA_AMP_Y * Screen.H * math.sin(2.0 * w * t),
    )


def make_saccade_targets(n):
    """Random positions inside the upper-left quadrant (screen centre origin, y up)."""
    targets = []
    while len(targets) < n:
        x = -random.uniform(0.08, 0.44) * Screen.W
        y = random.uniform(0.07, 0.42) * Screen.H
        if targets and math.hypot(x - targets[-1][0], y - targets[-1][1]) < TARGET_MIN_JUMP:
            continue
        targets.append((x, y))
    return targets


# ============================================================================
# 4. GAZE SOURCES
# ============================================================================
class TrackerGaze:
    """Tobii gaze stream; samples are (perf_counter time, x_pix, y_pix)."""

    def __init__(self, eyetracker):
        self._et = eyetracker
        self.samples = []
        self.active = False

    def start(self):
        self._et.subscribe_to(tr.EYETRACKER_GAZE_DATA, self._callback, as_dictionary=True)
        self.active = True

    def stop(self):
        if self.active:
            self._et.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self._callback)
        self.active = False

    def _callback(self, d):
        xs, ys = [], []
        if d["left_gaze_point_validity"]:
            xs.append(d["left_gaze_point_on_display_area"][0])
            ys.append(d["left_gaze_point_on_display_area"][1])
        if d["right_gaze_point_validity"]:
            xs.append(d["right_gaze_point_on_display_area"][0])
            ys.append(d["right_gaze_point_on_display_area"][1])
        if not xs:
            return
        nx, ny = sum(xs) / len(xs), sum(ys) / len(ys)
        if not (math.isfinite(nx) and math.isfinite(ny)):
            return
        px, py = norm_to_pix(nx, ny)
        self.samples.append((time.perf_counter(), px, py))

    def poll(self):
        pass


class MouseGaze:
    """Mouse-simulated gaze for testing without a tracker."""

    def __init__(self, win):
        self._mouse = event.Mouse(win=win)
        self.samples = []

    def start(self):
        pass

    def stop(self):
        pass

    def poll(self):
        x, y = self._mouse.getPos()
        self.samples.append((time.perf_counter(), float(x), float(y)))


def connect_eyetracker():
    if not TOBII_OK:
        return None
    try:
        trackers = tr.find_all_eyetrackers()
    except Exception as exc:
        print(f"[APP5] Tracker search failed: {exc}")
        return None
    if not trackers:
        return None
    et = trackers[0]
    print(f"Polaczono: {et.model} | SN: {et.serial_number}")
    return et


# ============================================================================
# 5. CALIBRATION
# ============================================================================
def show_text(win, text, height=30, color="white"):
    stim = visual.TextStim(win, text=text, color=color, height=height, wrapWidth=Screen.W * 0.8)
    stim.draw()
    win.flip()


def run_calibration(win, eyetracker):
    """Returns True (ok), False (failed) or None (escape)."""
    calibration = tr.ScreenBasedCalibration(eyetracker)
    calibration.enter_calibration_mode()

    ok_statuses = (
        tr.CALIBRATION_STATUS_SUCCESS,
        tr.CALIBRATION_STATUS_SUCCESS_LEFT_EYE,
        tr.CALIBRATION_STATUS_SUCCESS_RIGHT_EYE,
    )
    dot = visual.Circle(win, radius=20, fillColor="white", lineColor=None)
    center = visual.Circle(win, radius=4, fillColor="black", lineColor=None)

    success = False
    try:
        for attempt in range(3):
            failed = []
            for nx, ny in CAL_POINTS:
                px, py = norm_to_pix(nx, ny)
                # Let the eye land on the dot before sampling (~1 s).
                for frame in range(60):
                    dot.radius = max(8, 24 - frame * 0.27)
                    dot.pos = (px, py)
                    center.pos = (px, py)
                    dot.draw()
                    center.draw()
                    win.flip()
                    if "escape" in event.getKeys(["escape"]):
                        return None

                collected = False
                for _ in range(3):
                    if calibration.collect_data(nx, ny) in ok_statuses:
                        collected = True
                        break
                    core.wait(0.3)
                if not collected:
                    failed.append((nx, ny))

                dot.fillColor = "green" if collected else "red"
                dot.radius = 20
                dot.draw()
                center.draw()
                win.flip()
                core.wait(0.2)
                dot.fillColor = "white"

            result = calibration.compute_and_apply()
            if not failed and result.status in ok_statuses:
                success = True
                break
            print(f"[APP5] Calibration attempt {attempt + 1} failed (missing: {failed}, status: {result.status}).")
            for nx, ny in CAL_POINTS:
                calibration.discard_data(nx, ny)
    finally:
        calibration.leave_calibration_mode()
    return success


# ============================================================================
# 6. TRIAL
# ============================================================================
def wait_for_space(win, text):
    show_text(win, text)
    keys = event.waitKeys(keyList=["space", "escape"])
    return "escape" not in keys


def run_phase(win, gaze, duration, draw_frame):
    """Runs draw_frame(t) for `duration` seconds. Returns (t_start, t_end) or None on ESC."""
    event.clearEvents(eventType="keyboard")
    t0 = time.perf_counter()
    while True:
        t = time.perf_counter() - t0
        if t >= duration:
            break
        if "escape" in event.getKeys(["escape"]):
            return None
        gaze.poll()
        draw_frame(t)
        win.flip()
    return t0, time.perf_counter()


def run_trial(win, gaze):
    ball = visual.Circle(win, radius=BALL_RADIUS, fillColor="white", lineColor=None)
    gorilla = visual.Circle(win, radius=GORILLA_RADIUS, fillColor=GORILLA_COLOR, lineColor=None)

    # --- Phase 1: smooth pursuit
    def draw_pursuit(t):
        ball.pos = pursuit_pos(t)
        ball.draw()

    pursuit_span = run_phase(win, gaze, PURSUIT_SECONDS, draw_pursuit)
    if pursuit_span is None:
        return None

    # --- Phase 2: saccades + gorilla
    n_targets = int(round(SACCADE_SECONDS / (TARGET_ON + TARGET_OFF)))
    targets = make_saccade_targets(n_targets)
    cycle = TARGET_ON + TARGET_OFF

    def draw_saccade(t):
        gorilla.pos = gorilla_pos(t)
        gorilla.draw()
        idx = int(t // cycle)
        if idx < len(targets) and (t - idx * cycle) < TARGET_ON:
            ball.pos = targets[idx]
            ball.draw()

    saccade_span = run_phase(win, gaze, SACCADE_SECONDS, draw_saccade)
    if saccade_span is None:
        return None

    return {
        "pursuit_span": pursuit_span,
        "saccade_span": saccade_span,
        "targets": targets,
    }


def ask_gorilla(win):
    show_text(
        win,
        "Czy zauwazyl(a) Pan(i) w drugiej czesci cos oprocz pojawiajacej sie kropki?\n\n"
        "T = tak     N = nie",
    )
    keys = event.waitKeys(keyList=["t", "n", "escape"])
    if "escape" in keys:
        return None
    return "t" in keys


# ============================================================================
# 7. ANALYSIS
# ============================================================================
def slice_samples(samples, span):
    t0, t1 = span
    return [(t - t0, x, y) for (t, x, y) in samples if t0 <= t <= t1]


def count_saccades(samples):
    count = 0
    in_saccade = False
    for (t_a, x_a, y_a), (t_b, x_b, y_b) in zip(samples, samples[1:]):
        dt = t_b - t_a
        if dt <= 0:
            continue
        v = math.hypot(x_b - x_a, y_b - y_a) / dt
        if v > SACCADE_VELOCITY and not in_saccade:
            count += 1
            in_saccade = True
        elif v <= SACCADE_VELOCITY:
            in_saccade = False
    return count


def analyse(trial, all_samples):
    pur = slice_samples(all_samples, trial["pursuit_span"])
    sac = slice_samples(all_samples, trial["saccade_span"])
    res = {"pursuit_samples": pur, "saccade_samples": sac, "targets": trial["targets"]}

    # Smooth pursuit: distance between gaze and moving ball
    errs = []
    for t, x, y in pur:
        tx, ty = pursuit_pos(t)
        errs.append(math.hypot(x - tx, y - ty))
    res["pursuit_n"] = len(pur)
    if errs:
        res["pursuit_mean_err"] = sum(errs) / len(errs)
        res["pursuit_rms_err"] = math.sqrt(sum(e * e for e in errs) / len(errs))
        res["pursuit_on_target"] = 100.0 * sum(1 for e in errs if e < 120) / len(errs)
    else:
        res["pursuit_mean_err"] = res["pursuit_rms_err"] = res["pursuit_on_target"] = None
    res["pursuit_catchup_saccades"] = count_saccades(pur)

    # Saccades: latency to reach each target
    cycle = TARGET_ON + TARGET_OFF
    latencies = []
    for i, (tx, ty) in enumerate(trial["targets"]):
        onset = i * cycle
        for t, x, y in sac:
            if t < onset:
                continue
            if t > onset + cycle:
                break
            if math.hypot(x - tx, y - ty) < TARGET_HIT_RADIUS:
                latencies.append(t - onset)
                break
    res["targets_total"] = len(trial["targets"])
    res["targets_hit"] = len(latencies)
    res["latency_mean"] = (sum(latencies) / len(latencies)) if latencies else None
    res["saccade_count"] = count_saccades(sac)

    # Gorilla: gaze dwell near the gorilla path
    gcx, gcy = gorilla_center()
    half_w = GORILLA_AMP_X * Screen.W + GORILLA_MARGIN
    half_h = GORILLA_AMP_Y * Screen.H + GORILLA_MARGIN
    dwell = 0.0
    first_look = None
    for (t_a, _, _), (t_b, x_b, y_b) in zip(sac, sac[1:]):
        if abs(x_b - gcx) <= half_w and abs(y_b - gcy) <= half_h:
            dwell += min(0.05, t_b - t_a)
            if first_look is None:
                first_look = t_b
    res["gorilla_dwell"] = dwell
    res["gorilla_first_look"] = first_look
    res["gorilla_seen_gaze"] = dwell >= GORILLA_SEEN_DWELL
    return res


def save_session(res, self_report):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = HERE / f"app5_session_{ts}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["phase", "t_s", "x_px", "y_px"])
        for t, x, y in res["pursuit_samples"]:
            w.writerow(["pursuit", f"{t:.4f}", f"{x:.1f}", f"{y:.1f}"])
        for t, x, y in res["saccade_samples"]:
            w.writerow(["saccade", f"{t:.4f}", f"{x:.1f}", f"{y:.1f}"])
        w.writerow([])
        w.writerow(["metric", "value"])
        for key in (
            "pursuit_n", "pursuit_mean_err", "pursuit_rms_err", "pursuit_on_target",
            "pursuit_catchup_saccades", "targets_total", "targets_hit", "latency_mean",
            "saccade_count", "gorilla_dwell", "gorilla_first_look", "gorilla_seen_gaze",
        ):
            w.writerow([key, res[key]])
        w.writerow(["gorilla_self_report", self_report])
    return path


# ============================================================================
# 8. RESULTS VIEW
# ============================================================================
PANEL_SCALE = 0.45


def _fmt(v, fmt="{:.0f}", none="brak"):
    return none if v is None else fmt.format(v)


def _path_stim(win, pts, cx, cy, color, width=2):
    if len(pts) < 2:
        return None
    step = max(1, len(pts) // 600)
    verts = [(cx + x * PANEL_SCALE, cy + y * PANEL_SCALE) for _, x, y in pts[::step]]
    return visual.ShapeStim(
        win, vertices=verts, closeShape=False, lineColor=color, lineWidth=width, fillColor=None
    )


def show_results(win, res, self_report):
    W, H = Screen.W, Screen.H
    pw, ph = W * PANEL_SCALE, H * PANEL_SCALE
    py = 0.08 * H
    left_c = (-0.25 * W, py)
    right_c = (0.25 * W, py)

    stims = []

    def txt(text, pos, height=20, color="white", anchor="center", wrap=None):
        stims.append(visual.TextStim(
            win, text=text, pos=pos, height=height, color=color,
            alignText="left" if anchor == "left" else "center",
            anchorHoriz=anchor, wrapWidth=wrap or W * 0.45,
        ))

    def frame(c, title):
        stims.append(visual.Rect(win, width=pw, height=ph, pos=c, lineColor="grey", fillColor=None))
        txt(title, (c[0], c[1] + ph / 2 + 22), height=22)

    txt("WYNIKI", (0, 0.46 * H), height=34)
    frame(left_c, f"Sledzenie plynne ({int(PURSUIT_SECONDS)} s)")
    frame(right_c, f"Sakkady + goryl ({int(SACCADE_SECONDS)} s)")

    # Left panel: target path (dim) + gaze path
    tpath = [(0, *pursuit_pos(i * PURSUIT_PERIOD / 200.0)) for i in range(201)]
    s = _path_stim(win, tpath, left_c[0], left_c[1], [-0.3, -0.3, -0.3], 1)
    if s:
        stims.append(s)
    s = _path_stim(win, res["pursuit_samples"], left_c[0], left_c[1], [0.2, 0.9, 1.0], 2)
    if s:
        stims.append(s)

    # Right panel: gorilla path, saccade targets, gaze path
    gpath = [(0, *gorilla_pos(i * GORILLA_PERIOD / 100.0)) for i in range(101)]
    s = _path_stim(win, gpath, right_c[0], right_c[1], [-0.35, -0.35, -0.35], 2)
    if s:
        stims.append(s)
    for tx, ty in res["targets"]:
        stims.append(visual.Circle(
            win, radius=8, pos=(right_c[0] + tx * PANEL_SCALE, right_c[1] + ty * PANEL_SCALE),
            fillColor=None, lineColor="lime", lineWidth=2,
        ))
    s = _path_stim(win, res["saccade_samples"], right_c[0], right_c[1], [1.0, 0.85, 0.2], 2)
    if s:
        stims.append(s)
    gx, gy = gorilla_center()
    txt("goryl", (right_c[0] + gx * PANEL_SCALE, right_c[1] + (gy - 0.12 * H) * PANEL_SCALE),
        height=14, color=[-0.1, -0.1, -0.1])

    # Stats
    ty = py - ph / 2 - 85
    txt(
        "Probki: {}\nSredni blad: {} px\nRMS bledu: {} px\nNa celu (<120 px): {}%\nSakkady korekcyjne: {}".format(
            res["pursuit_n"], _fmt(res["pursuit_mean_err"]), _fmt(res["pursuit_rms_err"]),
            _fmt(res["pursuit_on_target"]), res["pursuit_catchup_saccades"],
        ),
        (left_c[0] - pw / 2, ty), anchor="left", height=20, wrap=pw,
    )
    txt(
        "Cele osiagniete: {}/{}\nSredni czas reakcji: {} s\nWykryte sakkady: {}\nCzas patrzenia na goryla: {:.2f} s".format(
            res["targets_hit"], res["targets_total"], _fmt(res["latency_mean"], "{:.2f}"),
            res["saccade_count"], res["gorilla_dwell"],
        ),
        (right_c[0] - pw / 2, ty), anchor="left", height=20, wrap=pw,
    )

    gaze_txt = "TAK (wzrok)" if res["gorilla_seen_gaze"] else "NIE (wzrok)"
    report_txt = {True: "TAK", False: "NIE", None: "brak"}[self_report]
    seen = res["gorilla_seen_gaze"] or self_report is True
    color = "lime" if seen else "orange"
    txt(
        f"GORYL ZAUWAZONY? {gaze_txt} | zgloszenie badanego: {report_txt}",
        (0, -0.40 * H), height=28, color=color, wrap=W * 0.9,
    )
    txt("Nacisnij SPACJE lub ESC, aby zakonczyc", (0, -0.46 * H), height=16, color="grey")

    event.clearEvents(eventType="keyboard")
    while True:
        for stim in stims:
            stim.draw()
        win.flip()
        if event.getKeys(["space", "escape"]):
            break


# ============================================================================
# 9. MAIN
# ============================================================================
def main():
    eyetracker = connect_eyetracker()
    simulated = eyetracker is None
    if simulated:
        print("Brak eye-trackera - tryb symulacji (mysz).")

    win = visual.Window(
        size=(1920, 1080), units="pix", fullscr=FULLSCREEN,
        color=[-1, -1, -1], waitBlanking=True,
    )
    Screen.update(win)
    win.mouseVisible = simulated

    try:
        intro = (
            "APP 5: PLYNNE SLEDZENIE I GORYL\n\n"
            "1. Kalibracja\n"
            f"2. {int(PURSUIT_SECONDS)} s: sledz wzrokiem kropke poruszajaca sie jak nieskonczonosc\n"
            f"3. {int(SACCADE_SECONDS)} s: patrz na kropki pojawiajace sie w lewym gornym rogu\n\n"
            "SPACJA - start, ESC - wyjscie"
        )
        if not wait_for_space(win, intro):
            return

        if not simulated:
            while True:
                result = run_calibration(win, eyetracker)
                if result is None:
                    return
                if result:
                    break
                show_text(win, "Kalibracja nieudana.\n\nSPACJA - powtorz, ESC - wyjscie")
                if "escape" in event.waitKeys(keyList=["space", "escape"]):
                    return

        if not wait_for_space(win, "Kalibracja zakonczona.\n\nNacisnij SPACJE, aby rozpoczac zadanie."):
            return

        gaze = MouseGaze(win) if simulated else TrackerGaze(eyetracker)
        gaze.start()
        try:
            trial = run_trial(win, gaze)
        finally:
            gaze.stop()
        if trial is None:
            return

        self_report = ask_gorilla(win)
        res = analyse(trial, gaze.samples)
        path = save_session(res, self_report)
        print(f"[APP5] Zapisano: {path}")
        show_results(win, res, self_report)
    finally:
        win.close()
        core.quit()


if __name__ == "__main__":
    main()
