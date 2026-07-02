import json
import re
import speech_recognition as sr
from datetime import datetime

from dotenv import load_dotenv

from speak import speak
from app_control import apps
from web_search import WebSearchAssistant
from search import SummaryModule
from sentiment_analysis import SentimentAnalyzer
from memory_system import MemorySystem
from memory_enhancement import MemoryEnhancement
from presentation_assistant import PresentationAssistant
from chatbot import AvaBrain

load_dotenv()

WAKE_PHRASES = ("hello ava", "hi ava", "hey ava", "wake up ava")
EXIT_PHRASES = ("quit", "exit", "shutdown", "close ava")
SLEEP_PHRASES = ("stop", "goodbye", "bye", "stop listening", "go to sleep")
ACTION_WORDS = ("open", "start", "run", "launch", "close", "terminate", "play")


def normalize_command(command):
    return " ".join(command.lower().strip().split())


def is_wake_command(command):
    return any(phrase in command for phrase in WAKE_PHRASES)


def is_exit_command(command):
    return normalize_command(command) in EXIT_PHRASES


def is_sleep_command(command):
    return normalize_command(command) in SLEEP_PHRASES


def is_action_command(command):
    if command.startswith("exit ") or command.startswith("quit "):
        return True
    return any(f" {word} " in f" {command} " or command.startswith(f"{word} ") for word in ACTION_WORDS)


def ava_greeting():
    hour = datetime.now().hour
    if hour < 12:
        period = "Good morning"
    elif hour < 17:
        period = "Good afternoon"
    else:
        period = "Good evening"
    return f"{period}. I'm AVA, your personal AI assistant. How can I help you?"


class Ava:
    def __init__(self, calibrate_mic=True):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.mic = sr.Microphone()
        self.apps = apps()
        self.web_search = WebSearchAssistant()
        self.summary_module = SummaryModule()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.memory = MemorySystem("user")
        self.memory_enhancement = MemoryEnhancement("user123")
        self.responses = self.load_responses()
        self.presentation_assistant = PresentationAssistant()
        self.brain = AvaBrain(memory_system=self.memory)

        if calibrate_mic:
            with self.mic as source:
                print("Calibrating for ambient noise... Please wait.")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)

    def load_responses(self):
        try:
            with open("responses.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            default_responses = {
                "hello": "Hello! I'm AVA. How can I help you?",
                "hi": "Hi there! What can I do for you?",
                "hey": "Hey! I'm listening.",
                "how are you": "I'm functioning well, thank you for asking!",
                "what's your name": "My name is AVA — Advanced Virtual Assistant.",
                "who are you": "I'm AVA, your personal AI assistant.",
                "goodbye": "Goodbye! Have a great day!",
                "thanks": "You're welcome!",
                "thank you": "You're welcome! Let me know if you need anything else.",
            }
            with open("responses.json", "w", encoding="utf-8") as f:
                json.dump(default_responses, f, indent=4)
            return default_responses

    def listen(self):
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print("\nListening...")
                self.recognizer.pause_threshold = 1
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("Processing speech...")
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text.lower()
        except sr.WaitTimeoutError:
            print("Listening timed out. Please try again.")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio. Please try again.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None
        except Exception as e:
            print(f"Error during listening: {e}")
            return None

    def get_personal_response(self, command):
        if command in self.responses:
            return self.responses[command]
        for key, value in self.responses.items():
            if re.search(r"\b" + re.escape(key) + r"\b", command):
                return value
        return None

    def handle_time(self):
        now = datetime.now().strftime("%I:%M %p")
        return f"It's {now}."

    def handle_date(self):
        today = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {today}."

    def handle_remember(self, command):
        fact = re.sub(r"^remember(?:\s+that)?\s+", "", command).strip()
        if not fact:
            return "What would you like me to remember?"

        name_match = re.match(r"my name is (.+)", fact)
        if name_match:
            self.memory.add_personal_info("name", name_match.group(1).strip())
            return f"Got it! I'll remember your name is {name_match.group(1).strip()}."

        self.memory.add_learned_fact("user_facts", fact)
        return "Noted. I'll remember that."

    def handle_recall(self):
        parts = []
        name = self.memory.get_personal_info("name")
        if name:
            parts.append(f"Your name is {name}.")

        facts = self.memory.get_learned_facts("user_facts")
        if facts:
            parts.append("I also remember: " + "; ".join(facts[-5:]))

        if not parts:
            return "I don't have any personal details stored yet. Say 'remember that' followed by what you'd like me to keep."

        return " ".join(parts)

    def process_command(self, command):
        if not command:
            return "I didn't catch that. Could you repeat?"

        try:
            sentiment, score = self.sentiment_analyzer.analyze(command)
            print(f"Sentiment: {sentiment} (Score: {score})")

            command = normalize_command(command)

            if any(p in command for p in ("what time", "what's the time", "tell me the time")):
                return self.handle_time()
            if any(p in command for p in ("what date", "what's the date", "what day is it", "tell me the date")):
                return self.handle_date()
            if command.startswith("remember"):
                return self.handle_remember(command)
            if any(p in command for p in ("what do you know about me", "what do you remember", "recall my")):
                return self.handle_recall()

            if is_action_command(command):
                return self.apps.execute_command(command)

            if any(word in command for word in ("presentation", "slide", "pdf")):
                return self.presentation_assistant.process_command(command)

            if "search" in command and command.strip().startswith("search"):
                query = command.replace("search", "", 1).strip()
                return self.web_search.search_on_web(query)

            if command.startswith("summary"):
                return self.summary_module.process_summary_command(command)

            personal_response = self.get_personal_response(command)
            if personal_response and len(command.split()) <= 4:
                self.memory.add_conversation(command, personal_response)
                return personal_response

            response = self.brain.chat(command, sentiment=sentiment)
            self.memory.add_conversation(command, response)
            return response

        except Exception as e:
            print(f"Error processing command: {e}")
            return "I encountered an error. Please try again."


def main():
    print("Initializing AVA...")
    ava = Ava()
    print("Initialization complete.")

    active = True
    speak(ava_greeting())

    while True:
        try:
            command = ava.listen()

            if command is None:
                continue

            command = normalize_command(command)
            print("Recognized:", command)

            if is_exit_command(command):
                speak("Goodbye! Shutting down.")
                break

            if not active:
                if is_wake_command(command):
                    active = True
                    speak("Hello. I'm listening.")
                else:
                    print("Say 'Hey AVA' to wake me up, or 'quit' to exit.")
                continue

            if is_sleep_command(command):
                speak("Going to standby. Say hey AVA when you need me.")
                ava.brain.clear_session()
                active = False
                continue

            response = ava.process_command(command)
            print("AVA:", response)
            speak(response)

        except Exception as e:
            print(e)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        print("Shutting down AVA...")
