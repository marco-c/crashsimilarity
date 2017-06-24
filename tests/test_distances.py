import unittest

from crashsimilarity.models.distances import structural_word_distance, edit_distance, edit_distance_structural


class DistancesTest(unittest.TestCase):
    def test_structural_word_distance(self):
        ab = 'a::b'
        a = 'a'
        b = 'b'
        abc = 'a::b::c'
        abcd = 'a::b::c::d'
        empty = ''
        self.assertEqual(structural_word_distance(ab, empty), 1)
        self.assertEqual(structural_word_distance(empty, ab), 1)
        self.assertEqual(structural_word_distance(empty, empty), 0)
        self.assertAlmostEqual(structural_word_distance(ab, a), 0.5)
        self.assertAlmostEqual(structural_word_distance(a, abcd), 0.75)
        self.assertAlmostEqual(structural_word_distance(abc, abcd), 0.25)
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

    def test_structural_distances(self):
        trace1 = ['a::b::c', 'a::b::d', 'x::y']
        trace2 = ['a::b::d', 'a::b::e', 'x::y']
        trace3 = ['qqq', 'ww', 'xx::y']

        dist12 = edit_distance_structural(trace1, trace2)
        dist21 = edit_distance_structural(trace2, trace1)
        dist13 = edit_distance_structural(trace1, trace3)
        dist32 = edit_distance_structural(trace3, trace2)

        self.assertLess(dist12, dist13)
        self.assertLess(dist12, dist32)
        self.assertEqual(dist12, dist21)
