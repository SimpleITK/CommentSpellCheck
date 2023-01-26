import unittest
import subprocess
import os


class TestCodespell(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("Setting up codespell tests")

    @classmethod
    def tearDownClass(cls):
        print("Tearing down dicom2stl tests")

    def test_codespell(self):
        print("Codespell test")
        cwd = os.getcwd()
        print(cwd)
        runresult = subprocess.run(
            [
                "python",
                "codespell.py",
                "--verbose",
                "--dict",
                "tests/dict.txt",
                "tests/example.h"
            ]
        )
        print("Return code:", runresult.returncode)
        if runresult.returncode:
            self.fail("codespell process returned bad code")


