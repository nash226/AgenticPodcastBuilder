import unittest
from unittest.mock import MagicMock, patch

import llm_tools


class TestLlmTools(unittest.TestCase):
    def test_require_env_vars_raises_for_missing_values(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError) as context:
                llm_tools._require_env_vars("OPENAI_API_KEY")

        self.assertIn("OPENAI_API_KEY", str(context.exception))

    @patch("llm_tools.requests.get")
    def test_read_webpage_returns_clean_text(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        text = llm_tools.read_webpage("https://example.com")

        self.assertEqual(text, "Hello World")
        mock_get.assert_called_once()

    @patch("llm_tools.requests.get")
    def test_search_web_returns_links(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "items": [
                {"link": "https://example.com/one"},
                {"link": "https://example.com/two"},
            ]
        }
        mock_get.return_value = mock_response

        with patch.dict(
            "os.environ",
            {
                "GOOGLE_API_KEY": "test-google-key",
                "SEARCH_ENGINE_ID": "test-search-engine-id",
            },
            clear=True,
        ):
            links = llm_tools.search_web("latest ai podcast news")

        self.assertEqual(
            links,
            ["https://example.com/one", "https://example.com/two"],
        )
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
