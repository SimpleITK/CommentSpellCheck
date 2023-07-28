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

    def test_comment_spell_check(self):
        print("\nCommand_spell_check simple test")
        cwd = os.getcwd()
        print(cwd)
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
            ]
        )
        print("Return code:", runresult.returncode)
        if runresult.returncode:
            self.fail("Simple test: comment_spell_check.py process returned bad code")

        print("\nComment_spell_check test on itself")
        cwd = os.getcwd()
        print(cwd)
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
            ]
        )
        print("Return code:", runresult.returncode)
        if runresult.returncode:
            self.fail(
                "Self code test: comment_spell_check.py process returned bad code"
            )
