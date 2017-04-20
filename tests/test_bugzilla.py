import unittest

from crashsimilarity import bugzilla


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
        crash_signatures2 = [u'std::list<T>::clear', u'std::list<T>::clear | CDeviceChild<T>::~CDeviceChild<T>']
        resp = bugzilla.get_signatures_from_bug('1333486')
        resp2 = bugzilla.get_signatures_from_bug('1308863')
        self.assertEqual(resp, crash_signatures)
        self.assertEqual(resp2, crash_signatures2)
