import unittest
from pathlib import Path

from Faaiduck.dictionaries.default import faai


class FaaiduckDictionaryTest(unittest.TestCase):
    def test_single_syllable_uses_toneless_frequency_lookup(self):
        self.assertEqual(faai.lookup(("SDa",)), "{&霸}")
        self.assertEqual(faai.lookup_candidates(("SDa",))[:4], (
            "霸",
            "芭",
            "壩",
            "葩",
        ))

    def test_single_syllable_with_tone(self):
        self.assertEqual(faai.lookup(("SDa-W^",)), "{&芭}")
        self.assertEqual(faai.lookup(("SDa-GH^",)), "{&唄}")

    def test_disyllabic_frequency_output(self):
        self.assertEqual(faai.lookup(("SDa-Si",)), "{&巴士}")
        self.assertEqual(faai.lookup_candidates(("SDa-Si",))[:4], (
            "巴士",
            "巴絲",
            "罷市",
            "把屎",
        ))

    def test_multistroke_toneless_frequency_output(self):
        self.assertEqual(faai.lookup(("SDa", "Si")), "{&巴士}")
        self.assertEqual(faai.jyutping_from_outline(("SDa", "Si")), "baasi")

    def test_workbook_initial_examples(self):
        self.assertEqual(faai.lookup(("SDHa",)), "{&趴}")
        self.assertEqual(faai.lookup(("GWa",)), "{&瓜}")
        self.assertEqual(faai.lookup(("GWHa",)), "{&誇}")
        self.assertEqual(faai.lookup(("SDGg",)), "{&五}")

    def test_workbook_final_examples(self):
        self.assertEqual(faai.lookup(("Sajg",)), "{&山}")
        self.assertEqual(faai.lookup(("Siuj",)), "{&水}")
        self.assertEqual(faai.jyutping_from_outline(("Suw",)), "su")
        with self.assertRaises(KeyError):
            faai.lookup(("Suw",))

    def test_frequency_table_lookup(self):
        self.assertEqual(faai.outline_from_jyutping("sat6ci4"), ("Swj-SHi",))
        self.assertEqual(faai.lookup(("Swj-SHi",)), "{&實詞}")
        self.assertEqual(
            faai.outline_from_jyutping("deoi3bat1hei2"),
            ("Diuj-SDwj", "Hij-D^"),
        )
        self.assertEqual(faai.lookup(("Diuj-SDwj", "Hij-D^")), "{&對不起}")

    def test_reverse_lookup(self):
        self.assertEqual(faai.reverse_lookup("baa"), [("SDa",)])
        self.assertEqual(faai.reverse_lookup("baa1"), [("SDa-W^",)])
        self.assertEqual(faai.reverse_lookup("巴士"), [("SDa-Si",)])

    def test_loader_without_file_global(self):
        path = Path("Faaiduck/dictionaries/default/faai.py").resolve()
        namespace = {"__name__": "faai_without_file"}
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
        self.assertNotIn("__file__", namespace)
        self.assertEqual(namespace["lookup"](("SDa", "Si")), "{&巴士}")

    def test_loader_stack_with_dictionary_self_path(self):
        path = Path("Faaiduck/dictionaries/default/faai.py").resolve()
        namespace = {"__name__": "faai_stack_self_path"}
        exec(compile(path.read_text(encoding="utf-8"), "<string>", "exec"), namespace)

        class Dictionary:
            def __init__(self, dictionary_path):
                self.path = str(dictionary_path)

            def get(self, key):
                return namespace["lookup"](key)

        self.assertEqual(Dictionary(path).get(("SDa", "Si")), "{&巴士}")


if __name__ == "__main__":
    unittest.main()
