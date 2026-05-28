"""Dictionary functions for the Faaiduck theory tables.

Known entries are loaded lazily from ``frequency.csv`` and ranked by frequency.
Plover-facing lookup returns Chinese text only; helper functions expose the
phonetic Jyutping decoding for tests and future tools.
"""

from collections import defaultdict
import csv
from functools import lru_cache
from pathlib import Path
import re


LONGEST_KEY = 12
FREQUENCY_PATH = Path(__file__).with_name("frequency.csv")
JYUTPING_RE = re.compile(r"([a-z]+)([1-6])")

LEFT_INITIALS = {
    "": "",
    "D": "d",
    "DG": "m",
    "DH": "t",
    "DW": "n",
    "G": "g",
    "GH": "k",
    "GW": "gw",
    "GWH": "kw",
    "H": "h",
    "S": "s",
    "SD": "b",
    "SDG": "ng",
    "SDH": "p",
    "SDW": "j",
    "SG": "z",
    "SGH": "",
    "SH": "c",
    "SW": "l",
    "W": "w",
    "WH": "f",
}

FINALS = {
    "": "a",
    "a": "aa",
    "ag": "aang",
    "ai": "e",
    "aig": "eng",
    "aijg": "yun",
    "aiu": "m",
    "aiug": "ng",
    "aiw": "yu",
    "aiwg": "ek",
    "aiwj": "yut",
    "aj": "aai",
    "ajg": "aan",
    "au": "o",
    "aug": "ong",
    "auj": "oi",
    "aujg": "on",
    "auwg": "ok",
    "auwj": "ot",
    "auwjg": "aap",
    "aw": "aau",
    "awg": "aak",
    "awj": "aat",
    "awjg": "aam",
    "g": "ang",
    "i": "i",
    "ig": "ing",
    "ij": "ei",
    "ijg": "in",
    "iu": "eo",
    "iug": "ung",
    "iuj": "eoi",
    "iujg": "eon",
    "iuw": "ou",
    "iuwg": "uk",
    "iuwj": "eot",
    "iw": "iu",
    "iwg": "ik",
    "iwj": "it",
    "iwjg": "im",
    "j": "ai",
    "jg": "an",
    "u": "oe",
    "ug": "oeng",
    "uj": "ui",
    "ujg": "un",
    "uw": "u",
    "uwg": "oek",
    "uwj": "ut",
    "uwjg": "ap",
    "w": "au",
    "wg": "ak",
    "wj": "at",
    "wjg": "am",
}

SPECIAL_SYLLABLES = {
    "aiu": "m",
    "SDGg": "ng",
}

TONES = {
    "W^": "1",
    "D^": "2",
    "H^": "3",
    "G^": "4",
    "WH^": "5",
    "GH^": "6",
}

TONE_TO_STROKE = {tone: stroke for stroke, tone in TONES.items()}
INITIAL_TO_STROKE = {
    initial: stroke for stroke, initial in LEFT_INITIALS.items() if initial
}
FINAL_TO_STROKE = {}
for _stroke, _final in FINALS.items():
    FINAL_TO_STROKE.setdefault(_final, _stroke)
SPECIAL_STROKE_TO_SYLLABLE = SPECIAL_SYLLABLES
SPECIAL_SYLLABLE_TO_STROKE = {
    syllable: stroke for stroke, syllable in SPECIAL_STROKE_TO_SYLLABLE.items()
}
SORTED_INITIALS = sorted(INITIAL_TO_STROKE, key=len, reverse=True)


def lookup(outline):
    assert len(outline) <= LONGEST_KEY
    honzi = lookup_honzi(outline)
    if honzi is not None:
        return _glue(honzi)
    raise KeyError


def reverse_lookup(text):
    text = text.strip("{}&")
    strokes = reverse_lookup_honzi(text)
    if strokes:
        return strokes

    if "/" in text:
        return []
    if "-" in text:
        left_text, right_text = text.split("-", 1)
        left_stroke = _reverse_syllable(left_text)
        right_stroke = _reverse_syllable(right_text)
        if left_stroke and right_stroke:
            return [(f"{left_stroke}-{right_stroke}",)]
        return []
    if text and text[-1:].isdigit():
        syllable = text[:-1]
        tone = text[-1]
        left_stroke = _reverse_syllable(syllable)
        tone_stroke = _reverse_tone(tone)
        if left_stroke and tone_stroke:
            return [(f"{left_stroke}-{tone_stroke}",)]
    stroke = _reverse_syllable(text)
    return [(stroke,)] if stroke else []


def lookup_honzi(outline, candidate=0):
    candidates = lookup_candidates(outline)
    if candidate < len(candidates):
        return candidates[candidate]
    return None


def lookup_candidates(outline):
    exact_candidates = _frequency_index().get(tuple(outline), ())
    if exact_candidates:
        return exact_candidates
    toneless = toneless_jyutping_from_outline(outline)
    if toneless:
        return _toneless_frequency_index().get(toneless, ())
    return ()


def reverse_lookup_honzi(text):
    return _reverse_frequency_index().get(text, ())


def parse_jyutping(jyutping):
    syllables = JYUTPING_RE.findall(jyutping)
    if "".join(syllable + tone for syllable, tone in syllables) != jyutping:
        return ()
    return tuple(syllables)


def jyutping_from_outline(outline):
    pieces = [_lookup_stroke(stroke) for stroke in outline]
    if any(piece is None for piece in pieces):
        return ""
    return "".join(piece.replace("-", "") for piece in pieces)


def toneless_jyutping_from_outline(outline):
    return _strip_tones(jyutping_from_outline(outline))


def outline_from_jyutping(jyutping, mode="canonical"):
    syllables = parse_jyutping(jyutping)
    if not syllables:
        return ()
    if mode == "full_tone":
        return tuple(
            _stroke_with_tone(syllable, tone) for syllable, tone in syllables
        )
    if mode != "canonical":
        raise ValueError(f"unknown outline mode: {mode}")

    strokes = []
    for index in range(0, len(syllables), 2):
        chunk = syllables[index:index + 2]
        if len(chunk) == 2:
            strokes.append(
                _stroke_pair(chunk[0][0], chunk[1][0])
            )
        else:
            strokes.append(_stroke_with_tone(chunk[0][0], chunk[0][1]))
    return tuple(strokes)


def stroke_for_jyutping_syllable(syllable):
    if syllable in SPECIAL_SYLLABLE_TO_STROKE:
        return SPECIAL_SYLLABLE_TO_STROKE[syllable]
    for initial in SORTED_INITIALS:
        if not syllable.startswith(initial):
            continue
        final = syllable[len(initial):]
        final_stroke = FINAL_TO_STROKE.get(final)
        if final_stroke is not None:
            return INITIAL_TO_STROKE[initial] + final_stroke
    final_stroke = FINAL_TO_STROKE.get(syllable)
    if final_stroke:
        return final_stroke
    return ""


def _lookup_stroke(stroke):
    left, right = _split_stroke(stroke)
    if right in TONES:
        syllable = _decode_syllable(left)
        if syllable:
            return syllable + TONES[right]
        return None

    left_syllable = _decode_syllable(left)
    right_syllable = _decode_syllable(right, right=True)

    if left_syllable and right_syllable:
        return left_syllable + "-" + right_syllable
    if left_syllable and not right:
        return left_syllable
    if right_syllable and not left:
        return right_syllable
    return None


def _stroke_pair(left_syllable, right_syllable):
    left = stroke_for_jyutping_syllable(left_syllable)
    right = stroke_for_jyutping_syllable(right_syllable)
    if not left or not right:
        return ""
    return left + "-" + right


def _stroke_with_tone(syllable, tone):
    stroke = stroke_for_jyutping_syllable(syllable)
    tone_stroke = TONE_TO_STROKE.get(tone, "")
    if not stroke or not tone_stroke:
        return ""
    return stroke + "-" + tone_stroke


def _split_stroke(stroke):
    if "-" in stroke:
        left, right = stroke.split("-", 1)
        return left, right
    return stroke, ""


def _decode_syllable(keys, right=False):
    if not keys:
        return ""
    if keys in SPECIAL_STROKE_TO_SYLLABLE:
        return SPECIAL_STROKE_TO_SYLLABLE[keys]

    for initial_stroke, initial in sorted(
        LEFT_INITIALS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if not keys.startswith(initial_stroke):
            continue
        final_stroke = keys[len(initial_stroke):]
        final = FINALS.get(final_stroke)
        if final is not None and (initial or final):
            return initial + final
    return ""


def _reverse_syllable(text):
    for special_stroke, special in SPECIAL_STROKE_TO_SYLLABLE.items():
        if text == special:
            return special_stroke
    for initial_stroke, initial in LEFT_INITIALS.items():
        if not text.startswith(initial):
            continue
        final_text = text[len(initial):]
        for final_stroke, final in FINALS.items():
            if final_text == final and (initial or final):
                return initial_stroke + final_stroke
    return ""


def _reverse_tone(tone):
    for stroke, value in TONES.items():
        if value == tone:
            return stroke
    return ""


@lru_cache(maxsize=1)
def _toneless_frequency_index():
    index = defaultdict(list)
    for row_number, row in enumerate(_load_frequency_rows()):
        toneless = _strip_tones(row["jyutping"])
        if toneless:
            index[toneless].append((row["frequency"], row_number, row["honzi"]))
    return _rank_index(index)


@lru_cache(maxsize=1)
def _frequency_index():
    index = defaultdict(list)
    for row_number, row in enumerate(_load_frequency_rows()):
        outlines = _outlines_for_row(row)
        for outline in outlines:
            if outline and all(outline):
                index[outline].append((row["frequency"], row_number, row["honzi"]))
    return _rank_index(index)


def _rank_index(index):
    ranked = {}
    for outline, entries in index.items():
        entries.sort(key=lambda entry: (-entry[0], entry[1]))
        words = []
        seen = set()
        for _, _, honzi in entries:
            if honzi in seen:
                continue
            words.append(honzi)
            seen.add(honzi)
        ranked[outline] = tuple(words)
    return ranked


@lru_cache(maxsize=1)
def _reverse_frequency_index():
    reverse = {}
    for row in _load_frequency_rows():
        outline = outline_from_jyutping(row["jyutping"])
        if outline:
            reverse.setdefault(row["honzi"], [outline])
    return {honzi: outlines for honzi, outlines in reverse.items()}


@lru_cache(maxsize=1)
def _load_frequency_rows():
    rows = []
    with FREQUENCY_PATH.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            rows.append({
                "honzi": row["honzi"],
                "jyutping": row["jyutping"],
                "frequency": _frequency(row["frequency"]),
            })
    return tuple(rows)


def _outlines_for_row(row):
    outlines = []
    canonical = outline_from_jyutping(row["jyutping"])
    if canonical:
        outlines.append(canonical)
    full_tone = outline_from_jyutping(row["jyutping"], mode="full_tone")
    if full_tone and full_tone != canonical:
        outlines.append(full_tone)
    return tuple(outlines)


def _frequency(value):
    try:
        return int(value)
    except ValueError:
        return 0


def _strip_tones(jyutping):
    syllables = parse_jyutping(jyutping)
    if syllables:
        return "".join(syllable for syllable, _ in syllables)
    return jyutping if jyutping.isalpha() else ""


def _glue(text):
    return "{&" + text + "}"
