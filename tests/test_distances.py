import unittest

from crashsimilarity.models.distances import structural_word_distance, edit_distance


class DistancesTest(unittest.TestCase):
    def test_structural_word_distance(self):
        ab = 'a::b'
        a = 'a'
        b = 'b'
        abc = 'a::b::c'
        empty = ''
        self.assertEqual(structural_word_distance(ab, empty), 1)
        self.assertEqual(structural_word_distance(empty, ab), 1)
        self.assertEqual(structural_word_distance(empty, empty), 0)
        self.assertAlmostEqual(structural_word_distance(ab, a), 0.5)
        self.assertEqual(structural_word_distance(ab, b), 1)
        self.assertAlmostEqual(structural_word_distance(ab, abc), 1 / 3)
        self.assertAlmostEqual(structural_word_distance(abc, ab), 1 / 3)

    def test_edit_distance_const_cost(self):
        abc = ['a', 'b', 'c']
        axc = ['a', 'x', 'c']
        axzc = ['a', 'x', 'z', 'c']
        aqzc = ['a', 'q', 'z', 'c']
        azc = ['a', 'z', 'c']
        bcd = ['b', 'c', 'd']
        ab = ['a', 'b']
        empty = []
        self.assertEqual(edit_distance(axzc, axzc), 0)
        self.assertEqual(edit_distance(abc, ab), 1)
        self.assertEqual(edit_distance(abc, bcd), 2)
        self.assertEqual(edit_distance(ab, bcd), 3)

        self.assertEqual(edit_distance(ab, empty), 2)
        self.assertEqual(edit_distance(abc, empty), 3)
        self.assertEqual(edit_distance(axzc, empty), 4)
        self.assertEqual(edit_distance(empty, empty), 0)

        self.assertEqual(edit_distance(axc, axzc), 1)
        self.assertEqual(edit_distance(axc, aqzc), 2)
        self.assertEqual(edit_distance(axzc, azc), 1)
