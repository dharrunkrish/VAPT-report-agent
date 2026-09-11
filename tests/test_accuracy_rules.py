import unittest

import utils.llm as llm_module
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

    def test_groq_model_names_preserve_openai_gpt_oss_120b(self):
        self.assertEqual(normalize_model_name("openai/gpt-oss-120b"), "openai/gpt-oss-120b")
        self.assertEqual(normalize_model_name("groq/llama-3.3-70b-versatile"), "groq/llama-3.3-70b-versatile")
        self.assertEqual(normalize_model_name("llama-3.3-70b-versatile"), "groq/llama-3.3-70b-versatile")
        self.assertEqual(normalize_model_name(""), "openai/gpt-oss-120b")

    def test_get_llm_sets_groq_openai_compatible_base_url(self):
        captured = {}

        class DummyLLM:
            def __init__(self, **kwargs):
                captured.update(kwargs)
                self._structured_outputs_disabled = False

        original_llm = llm_module.LLM
        try:
            llm_module.LLM = DummyLLM
            llm_module._shared_llm = None
            llm_module.get_llm(temperature=0.2, force_new=True)
        finally:
            llm_module.LLM = original_llm
            llm_module._shared_llm = None

        self.assertEqual(captured["model"], "openai/gpt-oss-120b")
        self.assertEqual(captured["api_key"], llm_module.GROQ_API_KEY)
        self.assertEqual(captured["base_url"], "https://api.groq.com/openai/v1")
        self.assertEqual(captured["custom_llm_provider"], "groq")
        self.assertEqual(captured["tool_choice"], "none")


if __name__ == "__main__":
    unittest.main()
