# fmt: off
KEYS = (
    "#-",
    "S-", "D-", "G-", "W-", "H-", "a-", "i-", "u-", "w-", "j-", "g-",
    "-S", "-D", "-G", "-W", "-H", "-a", "-i", "-u", "-w", "-j", "-g",
    "*", "^",
)
# fmt: on

IMPLICIT_HYPHEN_KEYS = ()
SUFFIX_KEYS = ()

NUMBER_KEY = None
NUMBERS = {}

UNDO_STROKE_STENO = "*"

ORTHOGRAPHY_RULES = []
ORTHOGRAPHY_RULES_ALIASES = {}
ORTHOGRAPHY_WORDLIST = None

KEYMAPS = {
    "Gemini PR": {
        "#-": ("#1", "#2"),
        "S-": ("S1-", "S2-"),
        "D-": "T-",
        "G-": "K-",
        "W-": "P-",
        "H-": "W-",
        "a-": "H-",
        "i-": "R-",
        "u-": ("*1", "*2"),
        "w-": "#3",
        "j-": "A-",
        "g-": "O-",
        "-u": ("*3", "*4"),
        "-w": "#4",
        "-j": "-U",
        "-a": "-F",
        "-i": "-R",
        "-g": "-E",
        "-W": "-P",
        "-H": "-B",
        "-D": "-L",
        "-G": "-G",
        "-S": ("-T", "-S"),
        "*": "-D",
        "^": "-Z",
        "no-op": ("Fn", "pwr", "res1", "res2"),
    },
    "Plover HID": {
        "#-": ("#1", "#2"),
        "S-": ("S1-", "S2-"),
        "D-": "T-",
        "G-": "K-",
        "W-": "P-",
        "H-": "W-",
        "a-": "H-",
        "i-": "R-",
        "u-": ("*1", "*2"),
        "w-": "#3",
        "j-": "A-",
        "g-": "O-",
        "-u": ("*3", "*4"),
        "-w": "#4",
        "-j": "-U",
        "-a": "-F",
        "-i": "-R",
        "-g": "-E",
        "-W": "-P",
        "-H": "-B",
        "-D": "-L",
        "-G": "-G",
        "-S": ("-T", "-S"),
        "*": "-D",
        "^": "-Z",
        "no-op": (
            "X1", "X2", "X3", "X4", "X5", "X6",
            "X7", "X8", "X9", "X10", "X11", "X12",
            "X13", "X14", "X15", "X16", "X17", "X18",
            "X19", "X20", "X21", "X22", "X23", "X24",
            "X25", "X26",
        ),
    },
    "Keyboard": {
        "#-": ("1", "2"),
        "S-": ("q", "a"),
        "D-": "w",
        "G-": "s",
        "W-": "e",
        "H-": "d",
        "a-": "r",
        "i-": "f",
        "u-": ("t", "g"),
        "w-": "space",
        "j-": "v",
        "g-": "b",
        "-u": ("y", "h"),
        "-w": "Return",
        "-j": "m",
        "-a": "u",
        "-i": "j",
        "-g": "n",
        "-W": "i",
        "-H": "k",
        "-D": "o",
        "-G": "l",
        "-S": ("p", ";"),
        "*": "[",
        "^": "'",
        "arpeggiate": "]",
        "no-op": ("z", "x", "c", ",", ".", "/", "\\"),
    },
}

DICTIONARIES_ROOT = "asset:Faaiduck:dictionaries/default"
DEFAULT_DICTIONARIES = ("user.json", "commands.json", "faai.py")
