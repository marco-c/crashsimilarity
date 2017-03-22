import unittest
import crash_similarity
from crash_similarity_support import func, stack_trace, top_ten_stack_traces


class CrashSimilarityTest(unittest.TestCase):

    def test_clean_func(self):
        for f in func:
            resp = crash_similarity.clean_func(f)
            self.assertTrue(resp.islower())
            assert '\n' not in resp
            if '@0x' in f:
                self.assertEqual('@0x', resp[-3:])

    def test_preprocess_returns_top_ten_stack_traces(self):
        resp = crash_similarity.preprocess(stack_trace)
        self.assertEqual(len(resp), 10)
        self.assertEqual(resp, top_ten_stack_traces)

    def test_should_skip_returns_correct_boolean_value(self):
        for f in func:
            if 'xul.dll@' in f or 'XUL@' in f or 'libxul.so@' in f:
                self.assertTrue(crash_similarity.should_skip(f))
            else:
                self.assertFalse(crash_similarity.should_skip(f))


if __name__ == '__main__':
    unittest.main()
