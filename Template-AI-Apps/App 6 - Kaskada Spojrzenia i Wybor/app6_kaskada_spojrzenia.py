#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classroom demonstration of exposure duration and preference choice."""

import csv
import math
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from psychopy import core, event, logging, visual
except ImportError as exc:
    raise ImportError("Brak PsychoPy. Zainstaluj: pip install psychopy") from exc

logging.console.setLevel(logging.ERROR)

HERE = Path(__file__).resolve().parent
FULLSCREEN = True
N_PAIRS = 8
N_REPETITIONS = 6
LONG_SECONDS = 0.9
SHORT_SECONDS = 0.3
CONTROL_SECONDS = 0.6
FRAME_RATE_FALLBACK = 60.0

INK = "#172b3a"
MUTED = "#83919b"
ACCENT = "#38c6a2"
BACKGROUND = "#101820"
STIMULUS_COLOR = "#f3f0e8"


def make_polygon(rng, sides, phase, radius=0.12):
    """Create a reproducible, irregular but smooth-edged abstract shape."""
    vertices = []
    for index in range(sides):
        angle = phase + 2 * math.pi * index / sides
        distance = radius * rng.uniform(0.78, 1.0)
        vertices.append((math.cos(angle) * distance, math.sin(angle) * distance))
    return vertices


def condition_order(rng):
    """Return a shuffled, balanced list of manipulation and control trials."""
    conditions = ["unequal"] * (N_PAIRS // 2) + ["equal"] * (N_PAIRS // 2)
    rng.shuffle(conditions)
    return conditions


def summarize(rows):
    """Summarize choices without treating the small demonstration as an experiment."""
    unequal = [row for row in rows if row["condition"] == "unequal"]
    equal = [row for row in rows if row["condition"] == "equal"]
    chose_long = sum(row["chose_longer"] == "yes" for row in unequal)
    shifted_unequal = sum(row["choice_changed"] == "yes" for row in unequal)
    shifted_equal = sum(row["choice_changed"] == "yes" for row in equal)
    return {
        "unequal_n": len(unequal),
        "chose_long_n": chose_long,
        "chose_long_pct": 100 * chose_long / len(unequal) if unequal else 0,
        "shifted_unequal_n": shifted_unequal,
        "shifted_equal_n": shifted_equal,
    }


def save_session(participant_id, rows):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id = re.sub(r"[^A-Za-z0-9_-]+", "_", participant_id).strip("_") or "uczestnik"
    path = HERE / f"app6_session_{safe_id}_{timestamp}.csv"
    fieldnames = [
        "participant_id",
        "trial",
        "condition",
        "repetitions",
        "long_exposure_s",
        "short_exposure_s",
        "baseline_choice",
        "final_choice",
        "chose_longer",
        "choice_changed",
        "longer_stimulus",
        "first_presented",
        "frame_rate_hz",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({"participant_id": participant_id, **row})
    return path


def show_message(win, text, height=0.034, color=STIMULUS_COLOR):
    visual.TextStim(
        win,
        text=text,
        color=color,
        height=height,
        wrapWidth=1.22,
        alignText="center",
    ).draw()
    win.flip()


def wait_for_key(keys):
    event.clearEvents(eventType="keyboard")
    pressed = event.waitKeys(keyList=list(keys) + ["escape"])
    if "escape" in pressed:
        return None
    return pressed[0]


def show_pair(win, left_shape, right_shape, prompt, labels=True):
    visual.ShapeStim(
        win, vertices=left_shape, pos=(-0.25, -0.02), closeShape=True,
        fillColor=STIMULUS_COLOR, lineColor=STIMULUS_COLOR,
    ).draw()
    visual.ShapeStim(
        win, vertices=right_shape, pos=(0.25, -0.02), closeShape=True,
        fillColor=STIMULUS_COLOR, lineColor=STIMULUS_COLOR,
    ).draw()
    visual.TextStim(
        win, text=prompt, pos=(0, 0.34), color=STIMULUS_COLOR, height=0.035,
        wrapWidth=1.25,
    ).draw()
    if labels:
        for x, label in [(-0.25, "F  |  lewa figura"), (0.25, "J  |  prawa figura")]:
            visual.TextStim(
                win, text=label, pos=(x, -0.26), color=MUTED, height=0.025,
            ).draw()
    win.flip()


def ask_choice(win, left_shape, right_shape, prompt):
    show_pair(win, left_shape, right_shape, prompt)
    key = wait_for_key(("f", "j"))
    if key is None:
        return None
    return "left" if key == "f" else "right"


def present_shape(win, shape, duration_frames):
    """Show one shape for a fixed number of display refreshes."""
    stim = visual.ShapeStim(
        win, vertices=shape, closeShape=True, fillColor=STIMULUS_COLOR,
        lineColor=STIMULUS_COLOR,
    )
    event.clearEvents(eventType="keyboard")
    for _ in range(duration_frames):
        if "escape" in event.getKeys(keyList=["escape"]):
            return False
        stim.draw()
        win.flip()
    return True


def run_exposure_pair(win, shape_a, shape_b, condition, frame_rate, rng):
    if condition == "unequal":
        longer = rng.choice(("a", "b"))
        durations = {
            "a": LONG_SECONDS if longer == "a" else SHORT_SECONDS,
            "b": LONG_SECONDS if longer == "b" else SHORT_SECONDS,
        }
    else:
        longer = ""
        durations = {"a": CONTROL_SECONDS, "b": CONTROL_SECONDS}

    frames = {key: max(1, round(seconds * frame_rate)) for key, seconds in durations.items()}
    order = ["a", "b"] * (N_REPETITIONS // 2)
    if rng.choice((True, False)):
        order.reverse()

    for stimulus_id in order:
        shape = shape_a if stimulus_id == "a" else shape_b
        if not present_shape(win, shape, frames[stimulus_id]):
            return None

    return {
        "longer_stimulus": longer,
        "first_presented": order[0],
        "duration_frames": frames,
    }


def show_instructions(win):
    show_message(
        win,
        "APP 6: KASKADA SPOJRZENIA I WYBOR\n\n"
        "Za chwile zobaczysz abstrakcyjne figury.\n"
        "Najpierw wybierz te, ktora bardziej Ci sie podoba.\n"
        "Potem figury beda pokazywane pojedynczo i na przemian.\n"
        "Na koncu ponownie wybierzesz jedna z nich.\n\n"
        "F = lewa figura     J = prawa figura\n\n"
        "Wyniki zapisywane sa lokalnie w pliku CSV.\n"
        "To demonstracja dydaktyczna, nie badanie diagnostyczne.\n\n"
        "SPACJA - start     ESC - wyjscie",
    )
    return wait_for_key(("space",)) is not None


def collect_participant_id(win):
    show_message(
        win,
        "Wpisz krotki kod uczestnika (bez imienia ani nazwiska).\n\n"
        "Uzyj liter i cyfr; zatwierdz ENTER.\n"
        "ESC - wyjscie",
    )
    event.clearEvents(eventType="keyboard")
    participant_id = ""
    clock = core.Clock()
    while True:
        visual.TextStim(
            win,
            text=participant_id or "_",
            color=ACCENT,
            height=0.06,
            pos=(0, -0.08),
        ).draw()
        win.flip()
        keys = event.getKeys()
        for key in keys:
            if key == "escape":
                return None
            if key == "return":
                if participant_id:
                    return participant_id
            elif key == "backspace":
                participant_id = participant_id[:-1]
            elif len(key) == 1 and key.isalnum() and len(participant_id) < 16:
                participant_id += key
        if clock.getTime() > 300:
            raise TimeoutError("Przekroczono limit czasu na wpisanie kodu uczestnika.")


def run_trial(win, pair, condition, frame_rate, rng, trial_number):
    shape_a, shape_b = pair
    left_is_a = rng.choice((True, False))
    left_shape, right_shape = (shape_a, shape_b) if left_is_a else (shape_b, shape_a)

    baseline = ask_choice(
        win, left_shape, right_shape,
        f"Proba {trial_number}/{N_PAIRS}: ktora figura bardziej Ci sie podoba?",
    )
    if baseline is None:
        return None

    show_message(win, "Patrz na kazda figure, gdy pojawia sie na srodku.\n\nSPACJA - kontynuuj")
    if wait_for_key(("space",)) is None:
        return None

    exposure = run_exposure_pair(win, shape_a, shape_b, condition, frame_rate, rng)
    if exposure is None:
        return None

    final_choice = ask_choice(
        win, left_shape, right_shape,
        "Ktora figura bardziej Ci sie podoba teraz?",
    )
    if final_choice is None:
        return None

    baseline_stimulus = "a" if (baseline == "left") == left_is_a else "b"
    final_stimulus = "a" if (final_choice == "left") == left_is_a else "b"
    longer = exposure["longer_stimulus"]

    if condition == "unequal":
        chose_longer = "yes" if final_stimulus == longer else "no"
    else:
        chose_longer = "not_applicable"

    return {
        "trial": trial_number,
        "condition": condition,
        "repetitions": N_REPETITIONS,
        "long_exposure_s": LONG_SECONDS if condition == "unequal" else CONTROL_SECONDS,
        "short_exposure_s": SHORT_SECONDS if condition == "unequal" else CONTROL_SECONDS,
        "baseline_choice": baseline_stimulus,
        "final_choice": final_stimulus,
        "chose_longer": chose_longer,
        "choice_changed": "yes" if baseline_stimulus != final_stimulus else "no",
        "longer_stimulus": longer or "none",
        "first_presented": exposure["first_presented"],
        "frame_rate_hz": round(frame_rate, 2),
    }


def show_results(win, rows, summary, csv_path):
    show_message(
        win,
        "WYNIKI DEMONSTRACJI\n\n"
        f"Proby z dluzsza ekspozycja: wybor dluzszej figury w "
        f"{summary['chose_long_n']}/{summary['unequal_n']} przypadkach "
        f"({summary['chose_long_pct']:.0f}%).\n\n"
        f"Zmiana wyboru od poczatku do konca:\n"
        f"nierowna ekspozycja: {summary['shifted_unequal_n']}/{summary['unequal_n']}\n"
        f"rowna ekspozycja: {summary['shifted_equal_n']}/{len(rows) - summary['unequal_n']}\n\n"
        "Pojedynczy wynik nie dowodzi wplywu spojrzenia.\n"
        "Nie uzywalismy eye-trackera, a liczba prob jest mala.\n\n"
        f"Dane zapisano w:\n{csv_path.name}\n\n"
        "SPACJA - zakonczenie",
    )
    wait_for_key(("space",))


def main():
    rng = random.Random()
    win = visual.Window(
        size=(1280, 800),
        units="height",
        fullscr=FULLSCREEN,
        color=BACKGROUND,
        waitBlanking=True,
    )
    win.mouseVisible = False

    try:
        if not show_instructions(win):
            return
        participant_id = collect_participant_id(win)
        if participant_id is None:
            return

        measured_rate = win.getActualFrameRate(
            nIdentical=10, nMaxFrames=100, nWarmUpFrames=10, threshold=1
        )
        frame_rate = measured_rate or FRAME_RATE_FALLBACK

        shapes = []
        for _ in range(N_PAIRS * 2):
            shapes.append(
                make_polygon(
                    rng,
                    sides=rng.randint(5, 8),
                    phase=rng.uniform(0, 2 * math.pi),
                )
            )
        pairs = list(zip(shapes[::2], shapes[1::2]))
        conditions = condition_order(rng)
        rows = []

        for trial_number, (pair, condition) in enumerate(zip(pairs, conditions), start=1):
            row = run_trial(win, pair, condition, frame_rate, rng, trial_number)
            if row is None:
                return
            rows.append(row)

        try:
            csv_path = save_session(participant_id, rows)
        except OSError as exc:
            show_message(
                win,
                "Nie udalo sie zapisac wynikow.\n\n"
                f"{exc}\n\n"
                "Dane nie zostaly zapisane. Sprawdz uprawnienia do folderu.\n"
                "SPACJA - zakonczenie",
            )
            wait_for_key(("space",))
            return

        show_results(win, rows, summarize(rows), csv_path)
    finally:
        win.close()
        core.quit()


if __name__ == "__main__":
    main()
