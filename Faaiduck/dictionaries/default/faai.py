"""Debug dictionary for the Faaiduck theory tables.

The lookup output is Jyutping-flavoured debug text wrapped in Plover's glue
operator. This keeps early testing focused on stroke parsing and keymaps; the
real Cantonese word and phrase dictionaries can replace or sit in front of this
dictionary later.
"""

LONGEST_KEY = 4

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
    "": "",
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
    "HG^": "6",
}

LEFT_INITIAL_KEYS = tuple("SDGWH")
LEFT_FINAL_KEYS = tuple("aiuwjg")
RIGHT_SYLLABLE_KEYS = tuple("uwjaigWHDGS")


def lookup(outline):
    assert len(outline) <= LONGEST_KEY
    pieces = [_lookup_stroke(stroke) for stroke in outline]
    if any(piece is None for piece in pieces):
        raise KeyError
    return "{&" + "/".join(pieces) + "}"


def reverse_lookup(text):
    text = text.strip("{}&")
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


def _split_stroke(stroke):
    if "-" in stroke:
        left, right = stroke.split("-", 1)
        return left, right
    return stroke, ""


def _decode_syllable(keys, right=False):
    if not keys:
        return ""
    if keys in SPECIAL_SYLLABLES:
        return SPECIAL_SYLLABLES[keys]

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
    for special_stroke, special in SPECIAL_SYLLABLES.items():
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
