"""Simulate chatbot conversations without using the microphone."""
import unittest
from unittest.mock import patch, MagicMock

from main import (
    Ava,
    normalize_command,
    is_exit_command,
    is_sleep_command,
    is_wake_command,
)


def make_ava():
    """Create Ava without microphone calibration."""
    with patch("main.sr.Microphone"), patch("main.sr.Recognizer") as mock_recognizer:
        mock_recognizer.return_value.adjust_for_ambient_noise = MagicMock()
        return Ava()


class ChatbotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ava = make_ava()

    def test_greeting_responses(self):
        cases = [
            ("hello", "Hello! How can I help you?"),
            ("hi there", "Hi there! What can I do for you?"),
            ("how are you", "I'm functioning well, thank you for asking!"),
            ("what's your name", "My name is Ava, I'm an AI assistant."),
            ("thank you", "You're welcome! Let me know if you need anything else."),
        ]
        for command, expected in cases:
            with self.subTest(command=command):
                self.assertEqual(self.ava.process_command(command), expected)

    def test_unknown_chat_gets_fallback(self):
        response = self.ava.process_command("tell me a joke about robots")
        self.assertIn("tell me a joke about robots", response.lower())

    def test_search_routes_to_web_search(self):
        response = self.ava.process_command("search python tutorials")
        self.assertIn("Searching for", response)

    def test_sleep_and_exit_helpers(self):
        self.assertTrue(is_sleep_command("stop"))
        self.assertTrue(is_exit_command("quit"))
        self.assertFalse(is_exit_command("exit chrome"))
        self.assertTrue(is_wake_command("hello ava"))

    def test_sentiment_module_runs(self):
        sentiment, score = self.ava.sentiment_analyzer.analyze("I am very happy today")
        self.assertEqual(sentiment, "positive")
        self.assertGreater(score, 0)

    def test_memory_stores_unknown_messages(self):
        before = len(self.ava.memory.get_recent_conversations(100))
        self.ava.process_command("what is the capital of france")
        after = len(self.ava.memory.get_recent_conversations(100))
        self.assertEqual(after, before + 1)


if __name__ == "__main__":
    print("Running chatbot simulation tests...\n")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ChatbotTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
