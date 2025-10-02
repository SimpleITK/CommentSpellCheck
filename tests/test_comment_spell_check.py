"""Test suite for the comment_spell_check command line tool."""

# ==========================================================================
#
#   Copyright NumFOCUS
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0.txt
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ==========================================================================*/

import unittest
import subprocess


class TestCommentSpellCheck(unittest.TestCase):
    """Test class for comment_spell_check command line tool."""

    @classmethod
    def setUpClass(cls):
        """Setting up comment_spell_check tests"""
        return cls()

    @classmethod
    def tearDownClass(cls):
        """Tearing down comment_spell_check tests"""

    def test_basic(self):
        """Basic test"""
        runresult = subprocess.run(
            [
                "comment_spell_check",
                "--miss",
                "--dict",
                "../tests/dict.txt",
                "--prefix",
                "myprefix",
                "../tests/example.h",
            ],
            cwd="comment_spell_check",
            stdout=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(runresult.returncode, 0, runresult.stdout)

    def test_codebase(self):
        """Code base test"""
        runresult = subprocess.run(
            [
                "comment_spell_check",
                "--verbose",
                "--prefix",
                "myprefix",
                "--suffix",
                ".py",
                "--suffix",
                ".md",
                ".",
            ],
            cwd="comment_spell_check",
            stdout=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(runresult.returncode, 0, runresult.stdout)

    def test_version(self):
        """Version test"""
        runresult = subprocess.run(
            [
                "comment_spell_check",
                "--version",
            ],
            cwd="comment_spell_check",
            stdout=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(runresult.returncode, 0)

        version_string = str(runresult.stdout)
        self.assertNotEqual(
            version_string, "unknown", "version string contains 'unknown'"
        )

    def test_bibtex(self):
        """Bibtext test"""
        runresult = subprocess.run(
            [
                "comment_spell_check",
                "--bibtex",
                "../tests/itk.bib",
                "../tests/bibtest.py",
            ],
            cwd="comment_spell_check",
            stdout=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(runresult.returncode, 0, runresult.stdout)

    def test_url(self):
        """URL test"""
        url = (
            "https://raw.githubusercontent.com/SimpleITK/SimpleITK/"
            "refs/heads/main/.github/workflows/additional_dictionary.txt"
        )
        runresult = subprocess.run(
            [
                "comment_spell_check",
                "--dict",
                url,
                "../tests/urltest.py",
            ],
            cwd="comment_spell_check",
            stdout=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(runresult.returncode, 0, runresult.stdout)


if __name__ == "__main__":
    unittest.main()
