import unittest
from unittest.mock import patch
from ai_provider_manager import AIProviderManager

class TestAIProviderManager(unittest.TestCase):
    def test_init_with_ollama(self):
        manager = AIProviderManager("ollama")
        self.assertEqual(manager.model_name, "llama3.1:latest")

    def test_init_with_openai(self):
        manager = AIProviderManager("openai")
        self.assertEqual(manager.model_name, "gpt-4")

    def test_init_with_xai(self):
        manager = AIProviderManager("xai")
        self.assertEqual(manager.model_name, "grok-1")

    def test_unsupported_provider(self):
        with self.assertRaises(ValueError):
            AIProviderManager("unsupported")

    @patch("ollama.chat")
    def test_ollama_invoke(self, mock_ollama):
        mock_ollama.return_value = {"message": {"content": "Test changelog"}}
        manager = AIProviderManager("ollama")
        changes = {"added_files": ["test.py"]}
        result = manager.invoke(changes)
        self.assertEqual(result, "Test changelog")

    @patch("requests.post")
    def test_xai_invoke(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"choices": [{"message": {"content": "Test changelog"}}]}
        manager = AIProviderManager("xai")
        changes = {"added_files": ["test.py"]}
        result = manager.invoke(changes)
        self.assertEqual(result, "Test changelog")

    def test_prompt_generation(self):
        manager = AIProviderManager("ollama")
        changes = {
            "added_files": ["test.py"],
            "modified_files": ["main.py"],
            "deleted_files": ["old.py"],
            "breaking_changes": ["API change"],
            "commit_messages": ["Fixed bug"]
        }
        prompt = manager._create_changelog_prompt(changes)
        self.assertIn("New Files Added:\n- test.py", prompt)
        self.assertIn("Modified Files:\n- main.py", prompt)
        self.assertIn("Deleted Files:\n- old.py", prompt)
        self.assertIn("Breaking Changes:\n- API change", prompt)
        self.assertIn("Commit Messages:\n- Fixed bug", prompt)

if __name__ == "__main__":
    unittest.main()
