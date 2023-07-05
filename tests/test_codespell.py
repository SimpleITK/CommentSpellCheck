import unittest
import subprocess
import os


class TestCodespell(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("\nSetting up codespell tests")

    @classmethod
    def tearDownClass(cls):
        print("\nTearing down dicom2stl tests")

    def test_codespell(self):
        print("\nCodespell simple test")
        cwd = os.getcwd()
        print(cwd)
        runresult = subprocess.run(
            [
                "python",
                "codespell.py",
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
            self.fail("Simple test: codespell process returned bad code")

        print("\nCodespell test on itself")
        cwd = os.getcwd()
        print(cwd)
        runresult = subprocess.run(
            [
                "python",
                "codespell.py",
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
            self.fail("Self code test: codespell process returned bad code")
