"""Dictionary functions for the Faaiduck theory tables.

Known entries are loaded lazily from ``frequency.csv`` and ranked by frequency.
Plover-facing lookup returns Chinese text only; helper functions expose the
phonetic Jyutping decoding for tests and future tools.
"""

from collections import defaultdict
import csv
from functools import lru_cache
import importlib.util
import inspect
from pathlib import Path
import re


LONGEST_KEY = 12
FREQUENCY_PATH = None
JYUTPING_RE = re.compile(r"([a-z]+)([1-6])")
CANDIDATE_STROKE = "-^"
CANDIDATE_STROKES = (CANDIDATE_STROKE, "^")
MAX_PARTIAL_SYLLABLES = 4

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
    base_outline, candidate_offset = _candidate_request(outline)
    honzi = lookup_honzi(outline)
    if honzi is not None:
        return _glue(honzi)
    if candidate_offset:
        raise KeyError
    jyutping = jyutping_from_outline(base_outline)
    if jyutping:
        return _glue(jyutping)
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
    base_outline, candidate_offset = _candidate_request(outline)
    candidates = lookup_candidates(base_outline)
    candidate_index = candidate + candidate_offset
    if candidate_index < len(candidates):
        return candidates[candidate_index]
    return None


def lookup_candidates(outline):
    outline, _ = _candidate_request(outline)
    partial = partial_key_from_outline(outline)
    if partial and _is_incomplete_partial_key(partial):
        partial_candidates = _partial_candidates(partial)
        if partial_candidates:
            return partial_candidates

    jyutping = jyutping_from_outline(outline)
    if jyutping:
        has_explicit_tones = _outline_has_only_explicit_tones(outline)
        if has_explicit_tones:
            jyutping_candidates = _jyutping_frequency_index().get(jyutping, ())
            if jyutping_candidates:
                return jyutping_candidates
        toneless = _strip_tones(jyutping)
        if toneless and not _has_tone(jyutping):
            return _toneless_frequency_index().get(toneless, ())
        if has_explicit_tones:
            return ()

    exact_candidates = _frequency_index().get(tuple(outline), ())
    if exact_candidates:
        return exact_candidates

    if jyutping:
        toneless = _strip_tones(jyutping)
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


def partial_key_from_outline(outline):
    selectors = []
    multi_stroke = len(outline) > 1
    for stroke in outline:
        parsed = _partial_selectors_from_stroke(
            stroke,
            force_initial_for_bare=multi_stroke,
        )
        if not parsed:
            return ()
        selectors.extend(parsed)
    return tuple(selectors)


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


def _candidate_request(outline):
    outline = tuple(outline)
    candidate_count = 0
    while outline and outline[-1] in CANDIDATE_STROKES:
        candidate_count += 1
        outline = outline[:-1]
    return outline, candidate_count


def _outline_has_only_explicit_tones(outline):
    if not outline:
        return False
    for stroke in outline:
        left, right = _split_stroke(stroke)
        if right not in TONES or not _decode_syllable(left):
            return False
    return True


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


def _partial_selectors_from_stroke(stroke, force_initial_for_bare=False):
    left, right = _split_stroke(stroke)
    if right in TONES:
        syllable = _decode_syllable(left)
        if syllable:
            return (("tone", syllable + TONES[right]),)
        return ()

    if left and right:
        left_selector = _selector_from_side(left, paired=True)
        right_selector = _selector_from_side(right, paired=True)
        if left_selector and right_selector:
            return (left_selector, right_selector)
        return ()

    side = left or right
    selector = _selector_from_side(side, paired=force_initial_for_bare)
    return (selector,) if selector else ()


def _selector_from_side(keys, paired=False):
    if not keys:
        return ()
    if keys in SPECIAL_STROKE_TO_SYLLABLE:
        return ("syllable", SPECIAL_STROKE_TO_SYLLABLE[keys])

    for initial_stroke, initial in sorted(
        LEFT_INITIALS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if not initial or not keys.startswith(initial_stroke):
            continue
        final_stroke = keys[len(initial_stroke):]
        if paired and not final_stroke:
            return ("initial", initial)
        final = FINALS.get(final_stroke)
        if final is not None:
            return ("syllable", initial + final)

    final = FINALS.get(keys)
    if final:
        return ("syllable", final)
    return ()


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


@lru_cache(maxsize=256)
def _partial_candidates(partial):
    entries = []
    for row_number, row in enumerate(_load_frequency_rows()):
        syllables = parse_jyutping(row["jyutping"])
        if not syllables or len(syllables) > MAX_PARTIAL_SYLLABLES:
            continue
        if _partial_matches_syllables(partial, syllables):
            entries.append((row["frequency"], row_number, row["honzi"]))
    return _rank_entries(entries)


@lru_cache(maxsize=1)
def _jyutping_frequency_index():
    index = defaultdict(list)
    for row_number, row in enumerate(_load_frequency_rows()):
        if row["jyutping"]:
            index[row["jyutping"]].append(
                (row["frequency"], row_number, row["honzi"])
            )
    return _rank_index(index)


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
        ranked[outline] = _rank_entries(entries)
    return ranked


def _rank_entries(entries):
    entries.sort(key=lambda entry: (-entry[0], entry[1]))
    words = []
    seen = set()
    for _, _, honzi in entries:
        if honzi in seen:
            continue
        words.append(honzi)
        seen.add(honzi)
    return tuple(words)


def _is_incomplete_partial_key(partial):
    return any(selector[0] == "initial" for selector in partial)


def _partial_matches_syllables(partial, syllables):
    if len(partial) != len(syllables):
        return False
    for selector, (syllable, tone) in zip(partial, syllables):
        selector_type, selector_value = selector
        if selector_type == "initial":
            if _initial_from_syllable(syllable) != selector_value:
                return False
        elif selector_type == "syllable":
            if syllable != selector_value:
                return False
        elif selector_type == "tone":
            if syllable + tone != selector_value:
                return False
        else:
            return False
    return True


def _initial_from_syllable(syllable):
    if syllable in SPECIAL_SYLLABLE_TO_STROKE:
        return syllable
    for initial in SORTED_INITIALS:
        if syllable.startswith(initial):
            return initial
    return ""


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
    frequency_path = _frequency_path()
    rows = []
    with frequency_path.open(newline="", encoding="utf-8-sig") as handle:
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


def _frequency_path():
    global FREQUENCY_PATH
    if FREQUENCY_PATH is None:
        FREQUENCY_PATH = _dictionary_path().with_name("frequency.csv")
    return FREQUENCY_PATH


def _dictionary_path():
    candidates = []

    _add_path_candidate(candidates, globals().get("__file__"))

    spec = globals().get("__spec__")
    _add_path_candidate(candidates, getattr(spec, "origin", None))

    frame = inspect.currentframe()
    while frame is not None:
        for local_name in ("filename", "resource", "path"):
            _add_path_candidate(candidates, frame.f_locals.get(local_name))

        dictionary = frame.f_locals.get("self")
        for attr_name in ("path", "filename", "_filename"):
            _add_path_candidate(candidates, getattr(dictionary, attr_name, None))

        _add_path_candidate(candidates, frame.f_code.co_filename)
        frame = frame.f_back

    package_spec = importlib.util.find_spec("Faaiduck.dictionaries.default")
    package_paths = getattr(package_spec, "submodule_search_locations", None)
    if package_paths:
        for package_path in package_paths:
            _add_path_candidate(candidates, Path(package_path) / "faai.py")

    for candidate in candidates:
        if _has_frequency_sibling(candidate):
            return candidate

    raise RuntimeError(
        "could not locate faai.py to load frequency.csv; tried "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def _add_path_candidate(candidates, value):
    if not value:
        return
    if not isinstance(value, (str, Path)):
        return
    value = str(value)
    if value.startswith("<"):
        return
    if value.startswith("asset:"):
        try:
            from plover.resource import resource_filename
        except Exception:
            return
        value = resource_filename(value)
    path = Path(value).expanduser().resolve()
    if path.is_dir():
        path = path / "faai.py"
    if path not in candidates:
        candidates.append(path)


def _has_frequency_sibling(path):
    return path.name == "faai.py" and path.with_name("frequency.csv").exists()


def _strip_tones(jyutping):
    syllables = parse_jyutping(jyutping)
    if syllables:
        return "".join(syllable for syllable, _ in syllables)
    return jyutping if jyutping.isalpha() else ""


def _has_tone(jyutping):
    return any(character.isdigit() for character in jyutping)


def _glue(text):
    return "{&" + text + "}"
