import speech_recognition as sr
from speak import speak
from app_control import apps
from web_search import WebSearchAssistant
from search import SummaryModule
from sentiment_analysis import SentimentAnalyzer
from memory_system import MemorySystem
import json
import time
from memory_enhancement import MemoryEnhancement
from presentation_assistant import PresentationAssistant


class Ava:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300  # Adjust sensitivitycc
        self.recognizer.dynamic_energy_threshold = True
        self.mic = sr.Microphone()
        self.apps = apps()
        self.web_search = WebSearchAssistant()
        self.summary_module = SummaryModule()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.memory = MemorySystem("sam")
        self.memory_enhancement = MemoryEnhancement("user123")
        self.responses = self.load_responses()
        self.presentation_assistant = PresentationAssistant()
        
        # Adjust for ambient noise on startup
        with self.mic as source:
            print("Calibrating for ambient noise... Please wait.")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)

        
    def load_responses(self):
        try:
            with open('responses.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("responses.json not found. Creating default responses.")
            default_responses = {
                "hello": "Hello! How can I help you?",
                "hi": "Hi there! What can I do for you?",
                "hey": "Hey! How can I assist you?",
                "how are you": "I'm functioning well, thank you for asking!",
                "what's your name": "My name is Ava, I'm an AI assistant.",
                "goodbye": "Goodbye! Have a great day!",
                "thanks": "You're welcome! Is there anything else I can help you with?",
                "thank you": "You're welcome! Let me know if you need anything else."
            }
            with open('responses.json', 'w', encoding='utf-8') as f:
                json.dump(default_responses, f, indent=4)
            return default_responses

    def listen(self):
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration = 0.3)
                print("\nListening...")
                # audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                self.recognizer.pause_threshold = 1
                audio = self.recognizer.listen(
                    source,
                    timeout = 5,
                    phrase_time_limit = 8
                )
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
        # Check for exact matches first
        if command in self.responses:
            return self.responses[command]
        
        # Then check for partial matches
        for key, value in self.responses.items():
            if key in command:
                return value
        return None

    def process_command(self, command):
        if not command:
            return "I didn't catch that. Could you please repeat?"

        try:
            # Analyze sentiment
            sentiment, score = self.sentiment_analyzer.analyze(command)
            print(f"Sentiment: {sentiment} (Score: {score})")
            
            # Process app-related commands
            if any(word in command for word in ['open', 'start', 'run', 'launch', 'close', 'exit', 'quit', 'terminate']):
                return self.apps.execute_command(command)
            
            if any(word in command for word in ['presentation', 'slide', 'pdf']):
                return self.presentation_assistant.process_command(command)
            
            # Process web search commands
            elif 'search' in command:
                query = command.replace('search', '', 1).strip()
                return self.web_search.search_on_web(query)
            
            # Process summary requests
            elif command.startswith('summary'):
                return self.summary_module.process_summary_command(command)
            
            
            # Check for personal responses
            personal_response = self.get_personal_response(command)
            if personal_response:
                return personal_response
                
            # Store conversation in memory
            self.memory.add_conversation(command, "Processing your request...")
            
            # Default response
            return f"I understand you're saying something about {command}. How can I help you with that?"

        except Exception as e:
            print(f"Error processing command: {e}")
            return "I encountered an error while processing your request. Please try again."

def main():
    print("Initializing Ava...")
    ava = Ava()
    print("Initialization complete.")
    
    # speak("Hello! I am Ava, your AI assistant. How can I help you today?")
    
    # active = True
    # waiting_for_hello = False
    active = False

    while True:
        try:
            command = ava.listen()

            if command is None:
                continue

            print("Recognized:", command)

            if not active:
                if "hello ava" in command or "hi ava" in command:
                    active = True
                    speak("Hello. I am listening.")
                else:
                    continue

            if any(word in command for word in ['goodbye', 'bye', 'stop']):
                speak("Goodbye for now! I'll be here when you need me again.")
                active = False
                continue
            
            if any(word in command for word in ["quit", "exit"]):
                speak("Goodbye! Have a great day!")
                break
            
            response = ava.process_command(command)
            print("AVA:", response)
            speak(response)

        except Exception as e:
            print(e)
    
    # while True:
    #     try:
    #         if not active and not waiting_for_hello:
    #             speak("Say hello to start a new conversation.")
    #             waiting_for_hello = True
            
    #         command = ava.listen()
            
    #         if command:
    #             # Handle exit commands
    #             if any(word in command for word in ['goodbye', 'bye', 'exit', 'stop', 'quit']):
    #                 speak("Goodbye for now! I'll be here when you need me again.")
    #                 active = False
    #                 waiting_for_hello = False
    #                 continue
                
    #             # Handle hello when waiting
    #             if waiting_for_hello and any(word in command for word in ['hello', 'hi', 'hey']):
    #                 speak("Hello again! How can I assist you?")
    #                 active = True
    #                 waiting_for_hello = False
    #                 continue
                
    #             # Process normal commands when active
    #             if active:
    #                 response = ava.process_command(command)
    #                 speak(response)
                    
    #                 # Optional: Add a short pause between interactions
    #                 time.sleep(0.5)
            
    #         else:
    #             # If no command is detected, continue listening
    #             continue

    #     except Exception as e:
    #         print(f"Error in main loop: {e}")
    #         speak("I encountered an error. Please try again.")
    #         continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        print("Shutting down Ava...")