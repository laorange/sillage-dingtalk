import unittest

from . import dingTalkHandler


class DingTalkTester(unittest.TestCase):
    def test_access_Token(self):
        self.assertIsNone(dingTalkHandler.accessToken)


if __name__ == '__main__':
    unittest.main()
