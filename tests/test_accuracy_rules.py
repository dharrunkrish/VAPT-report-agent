import unittest

from utils.llm import normalize_model_name
from utils.schemas import ReportSection


class AccuracyRuleTests(unittest.TestCase):
    def test_uncertain_classifications_are_not_guessed(self):
        section = ReportSection(
            title="Sample finding",
            severity="Requires manual verification",
            cvss_score=None,
            cwe="Requires manual verification",
            owasp="Requires manual verification",
            wstg="Requires manual verification",
            description="No evidence supplied.",
            steps_to_reproduce=[],
            remediation=[],
        )

        self.assertEqual(section.severity, "Requires manual verification")
        self.assertEqual(section.cwe, "Requires manual verification")
        self.assertEqual(section.owasp, "Requires manual verification")
        self.assertEqual(section.wstg, "Requires manual verification")

    def test_groq_model_names_are_not_double_prefixed(self):
        self.assertEqual(normalize_model_name("openai/gpt-oss-120b"), "groq/gpt-oss-120b")
        self.assertEqual(normalize_model_name("groq/llama-3.3-70b-versatile"), "groq/llama-3.3-70b-versatile")
        self.assertEqual(normalize_model_name("llama-3.3-70b-versatile"), "groq/llama-3.3-70b-versatile")


if __name__ == "__main__":
    unittest.main()
