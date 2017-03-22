import unittest
import bugzilla


class BugzillaTest(unittest.TestCase):

    def test_get_signatures_from_bug(self):
        crash_signatures = [u'@0x0 | idmcchandler7_64.dll@0x238bf',
                            u'@0x0 | idmcchandler7_64.dll@0x1feaf',
                            u'@0x0 | idmcchandler7_64.dll@0x238bf',
                            u'@0x0 | idmcchandler7_64.dll@0x233af',
                            u'@0x0 | idmcchandler7_64.dll@0x233cf',
                            u'@0x0 | idmcchandler7_64.dll@0x22e6f',
                            u'@0x0 | idmcchandler7_64.dll@0x22e7f',
                            u'@0x0 | idmcchandler7_64.dll@0x2343f',
                            u'@0x0 | idmcchandler5_64.dll@0x1f0ea',
                            u'@0x0 | ffi_call']
        resp = bugzilla.get_signatures_from_bug('1333486')
        self.assertEqual(resp, crash_signatures)


if __name__ == '__main__':
    unittest.main()
