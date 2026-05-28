import unittest
import configparser
import json

from Faaiduck import system
from Faaiduck.dictionaries.default import faai


class FaaiduckSystemTest(unittest.TestCase):
    def test_plover_entry_point_target_exists(self):
        self.assertEqual(system.DICTIONARIES_ROOT, "asset:Faaiduck:dictionaries/default")
        self.assertIn("faai.py", system.DEFAULT_DICTIONARIES)

    def test_package_is_not_zip_safe(self):
        config = configparser.ConfigParser()
        config.read("setup.cfg")
        self.assertEqual(config["metadata"]["version"], "0.1.6")
        self.assertEqual(config["options"]["zip_safe"], "False")

    def test_requested_gemini_key_examples(self):
        gemini = system.KEYMAPS["Gemini PR"]
        self.assertEqual(gemini["w-"], "#3")
        self.assertEqual(gemini["-w"], "#4")
        self.assertEqual(gemini["S-"], ("S1-", "S2-"))
        self.assertEqual(gemini["D-"], "T-")
        self.assertEqual(gemini["-j"], "-U")
        self.assertEqual(gemini["-g"], "-E")

    def test_keymap_covers_all_system_keys(self):
        for machine, keymap in system.KEYMAPS.items():
            with self.subTest(machine=machine):
                missing = [key for key in system.KEYS if key not in keymap]
                self.assertEqual(missing, [])

    def test_default_commands_include_spacing_and_punctuation(self):
        with open("Faaiduck/dictionaries/default/commands.json", encoding="utf-8") as f:
            commands = json.load(f)
        self.assertEqual(commands["#-S"], "{^ ^}")
        self.assertEqual(commands["#-D"], "{#Return}")
        self.assertEqual(commands["#-G"], "{&。}")
        self.assertEqual(commands["#-W"], "{&，}")
        self.assertEqual(commands["#-WH"], "{&？}")
        self.assertNotIn(faai.CANDIDATE_STROKE, commands)


if __name__ == "__main__":
    unittest.main()
