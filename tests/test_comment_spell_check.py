import unittest
import subprocess
import os


class TestCommentSpellCheck(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("\nSetting up comment_spell_check tests")

    @classmethod
    def tearDownClass(cls):
        print("\nTearing down comment_spell_check tests")

    def test_basic(self):
        print("\nCommand_spell_check: Basic Test")
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
        if runresult.returncode:
            self.fail("\nBasic Test: FAIL")
            output_string = str(runresult.stdout)
            print("\nTest output:", output_string)

    def test_codebase(self):
        print("\nComment_spell_check: Code Base Test")
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
        if runresult.returncode:
            self.fail("\nCode Base Test: FAIL")
            output_string = str(runresult.stdout)
            print("\nTest output:", output_string)

    def test_version(self):
        print("\nComment_spell_check: Version Test")
        runresult = subprocess.run(
            [
                "python",
                "comment_spell_check.py",
                "--version",
            ],
            stdout=subprocess.PIPE,
        )
        version_string = str(runresult.stdout)
        if runresult.returncode:
            self.fail("Version Test: FAIL")
        if "unknown" in version_string:
            self.fail("Version Test: version string contains 'unknown'")
