import unittest

from Faaiduck.dictionaries.default import faai


class FaaiduckDictionaryTest(unittest.TestCase):
    def test_single_syllable(self):
        self.assertEqual(faai.lookup(("SDa",)), "{&baa}")

    def test_single_syllable_with_tone(self):
        self.assertEqual(faai.lookup(("SDa-W^",)), "{&baa1}")
        self.assertEqual(faai.lookup(("SDa-HG^",)), "{&baa6}")

    def test_disyllabic_debug_output(self):
        self.assertEqual(faai.lookup(("SDa-Si",)), "{&baa-si}")

    def test_workbook_initial_examples(self):
        self.assertEqual(faai.lookup(("SDHa",)), "{&paa}")
        self.assertEqual(faai.lookup(("GWa",)), "{&gwaa}")
        self.assertEqual(faai.lookup(("GWHa",)), "{&kwaa}")
        self.assertEqual(faai.lookup(("SDGg",)), "{&ng}")

    def test_workbook_final_examples(self):
        self.assertEqual(faai.lookup(("Sajg",)), "{&saan}")
        self.assertEqual(faai.lookup(("Siuj",)), "{&seoi}")
        self.assertEqual(faai.lookup(("Suw",)), "{&su}")

    def test_reverse_lookup(self):
        self.assertEqual(faai.reverse_lookup("baa"), [("SDa",)])
        self.assertEqual(faai.reverse_lookup("baa1"), [("SDa-W^",)])
        self.assertEqual(faai.reverse_lookup("baa-si"), [("SDa-Si",)])


if __name__ == "__main__":
    unittest.main()
