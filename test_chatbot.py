"""Simulate AVA chatbot conversations without using the microphone."""
import unittest
from unittest.mock import MagicMock, patch

from chatbot import AvaBrain
from main import (
    Ava,
    is_exit_command,
    is_sleep_command,
    is_wake_command,
    is_action_command,
)


def make_ava():
    with patch("main.sr.Microphone"), patch("main.sr.Recognizer") as mock_recognizer:
        mock_recognizer.return_value.adjust_for_ambient_noise = MagicMock()
        ava = Ava(calibrate_mic=False)
        ava.brain = MagicMock(spec=AvaBrain)
        ava.brain.chat.return_value = "Paris is the capital of France."
        return ava


class ChatbotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ava = make_ava()

    def test_greeting_responses(self):
        cases = [
            ("hello", "Hello! I'm AVA. How can I help you?"),
            ("how are you", "I'm functioning well, thank you for asking!"),
            ("what's your name", "My name is AVA — Advanced Virtual Assistant."),
            ("thank you", "You're welcome! Let me know if you need anything else."),
        ]
        for command, expected in cases:
            with self.subTest(command=command):
                self.assertEqual(self.ava.process_command(command), expected)

    def test_ai_chat_for_open_questions(self):
        response = self.ava.process_command("what is the capital of france")
        self.assertIn("paris", response.lower())
        self.ava.brain.chat.assert_called()

    def test_time_command(self):
        response = self.ava.process_command("what time is it")
        self.assertIn(":", response)

    def test_remember_and_recall(self):
        self.ava.process_command("remember that my name is Tony")
        response = self.ava.process_command("what do you know about me")
        self.assertIn("tony", response.lower())

    def test_search_routes_to_web_search(self):
        response = self.ava.process_command("search python tutorials")
        self.assertIn("Searching for", response)

    def test_sleep_and_exit_helpers(self):
        self.assertTrue(is_sleep_command("stop"))
        self.assertTrue(is_exit_command("quit"))
        self.assertFalse(is_exit_command("exit chrome"))
        self.assertTrue(is_wake_command("hey ava"))
        self.assertTrue(is_action_command("open notepad"))

    def test_sentiment_module_runs(self):
        sentiment, score = self.ava.sentiment_analyzer.analyze("I am very happy today")
        self.assertEqual(sentiment, "positive")
        self.assertGreater(score, 0)


if __name__ == "__main__":
    print("Running AVA chatbot tests...\n")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ChatbotTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
