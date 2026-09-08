import ast
from pathlib import Path
import unittest


class ModelValidationTests(unittest.TestCase):
    def setUp(self):
        # Load the real helpers without starting the Discord bot or loading keys.
        source = ast.parse(Path(__file__).with_name("Bot.py").read_text())
        helpers = ast.Module(body=[
            node for node in source.body
            if isinstance(node, ast.FunctionDef)
            and node.name in {"clean_model", "is_valid_model", "_cache_get_instant"}
        ], type_ignores=[])
        self.scope = {
            "KNOWN_MODELS": {"text": ["openai"], "image": ["flux"]},
            "MODEL_DISPLAY_TO_ID": {"Flux (PAID)": "flux"},
            "MODEL_CACHE": {"pollinations:image": {"models": ["black-forest-labs/flux.1-schnell"]}},
        }
        exec(compile(helpers, "Bot.py", "exec"), self.scope)

    def test_accepts_names_offered_by_live_autocomplete(self):
        self.assertTrue(self.scope["is_valid_model"]("image", "black-forest-labs/flux.1-schnell"))

    def test_preserves_legacy_ids_and_display_names(self):
        for model in ["flux", "Flux (PAID)"]:
            self.assertTrue(self.scope["is_valid_model"]("image", model))

    def test_rejects_unknown_and_wrong_category(self):
        self.assertFalse(self.scope["is_valid_model"]("image", "unknown"))
        self.assertFalse(self.scope["is_valid_model"]("text", "black-forest-labs/flux.1-schnell"))

    def test_cold_cache_keeps_static_validation(self):
        self.scope["MODEL_CACHE"].clear()
        self.assertTrue(self.scope["is_valid_model"]("image", "flux"))
        self.assertFalse(self.scope["is_valid_model"]("image", "unknown"))


if __name__ == "__main__":
    unittest.main()
