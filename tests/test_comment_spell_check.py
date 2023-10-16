import unittest
import subprocess


class TestCommentSpellCheck(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        """Setting up comment_spell_check tests"""

    @classmethod
    def tearDownClass(cls):
        """Tearing down comment_spell_check tests"""

    def test_basic(self):
        """Basic test"""
        runresult = subprocess.run(
            [
                "python",
                "comment_spell_check.py",
                "--verbose",
                "--dict",
                "tests/dict.txt",
                "--prefix",
                "myprefix",
                "tests/example.h",
            ],
            stdout=subprocess.PIPE,
        )
        self.assertEqual(
            runresult.returncode, 0, "Basic test FAIL: " + str(runresult.stdout)
        )

    def test_codebase(self):
        """Code base test"""
        runresult = subprocess.run(
            [
                "python",
                "comment_spell_check.py",
                "--verbose",
                "--prefix",
                "myprefix",
                "--suffix",
                ".py",
                "--suffix",
                ".md",
                ".",
            ],
            stdout=subprocess.PIPE,
        )
        self.assertEqual(
            runresult.returncode, 0, "Code test FAIL: " + str(runresult.stdout)
        )

    def test_version(self):
        """Version test"""
        runresult = subprocess.run(
            [
                "python",
                "comment_spell_check.py",
                "--version",
            ],
            stdout=subprocess.PIPE,
        )
        self.assertEqual(runresult.returncode, 0, "Version test FAIL")

        version_string = str(runresult.stdout)
        self.assertNotEqual(
            version_string, "unknown", "version string contains 'unknown'"
        )
