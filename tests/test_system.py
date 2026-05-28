import unittest

from Faaiduck import system


class FaaiduckSystemTest(unittest.TestCase):
    def test_plover_entry_point_target_exists(self):
        self.assertEqual(system.DICTIONARIES_ROOT, "asset:Faaiduck:dictionaries/default")
        self.assertIn("faai.py", system.DEFAULT_DICTIONARIES)

    def test_requested_gemini_key_examples(self):
        gemini = system.KEYMAPS["Gemini PR"]
        self.assertEqual(gemini["w-"], "#3")
        self.assertEqual(gemini["-w"], "#4")
        self.assertEqual(gemini["S-"], ("S1-", "S2-"))
        self.assertEqual(gemini["D-"], "T-")

    def test_keymap_covers_all_system_keys(self):
        for machine, keymap in system.KEYMAPS.items():
            with self.subTest(machine=machine):
                missing = [key for key in system.KEYS if key not in keymap]
                self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
