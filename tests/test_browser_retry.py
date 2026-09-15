"""Regression tests for the bounded browser startup retry policy."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/browser_release.mjs").read_text()


class BrowserRetryPolicyTests(unittest.TestCase):
    def test_retry_is_bounded_to_one_extra_attempt(self):
        self.assertIn("const MAX_START_ATTEMPTS=2;", SCRIPT)
        self.assertIn("for(let attempt=1;attempt<=MAX_START_ATTEMPTS;attempt++)", SCRIPT)

    def test_only_start_timeout_is_retryable(self):
        self.assertIn("e?.message==='start timeout'&&attempt<MAX_START_ATTEMPTS", SCRIPT)
        self.assertIn("BROWSER CHECK FAILED: ", SCRIPT)

    def test_each_attempt_uses_a_clean_profile(self):
        self.assertIn("async function runBrowserCheck()", SCRIPT)
        self.assertIn("mkdtemp(join(tmpdir(),'macro-release-'))", SCRIPT)
        self.assertIn("rm(profile,{recursive:true,force:true})", SCRIPT)

    def test_validation_rules_are_not_relaxed(self):
        self.assertIn("unexpected.length", SCRIPT)
        self.assertIn("errors.length", SCRIPT)
        self.assertIn("document.querySelectorAll('.panel').length===9", SCRIPT)
        self.assertIn("Network.setBlockedURLs", SCRIPT)


if __name__ == "__main__":
    unittest.main()
