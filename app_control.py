import os
import subprocess
import psutil
import speech_recognition as sr
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from speak import speak

class apps:
    def __init__(self):
        self.app_cache = {}
        self.spotify = None
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()

    def initialize_spotify(self):
        scope = "user-read-playback-state,user-modify-playback-state"
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    def find_app(self, app_name):
        if app_name in self.app_cache:
            return self.app_cache[app_name]
        
            # Check for Photoshop specifically
        if "photoshop" in app_name.lower():
            photoshop_path = r"D:\PSCC 2019\PSCC 2019\Adobe Photoshop CC 2019\Photoshop.exe"
            if os.path.exists(photoshop_path):
                self.app_cache[app_name] = photoshop_path
                return photoshop_path
            
        # Check for After Effects specifically
        if "after effects" in app_name.lower():
            after_effects_path = r"D:\AE 2019 CC\Adobe After Effects CC 2019\Support Files\AfterFX.exe"
            if os.path.exists(after_effects_path):
                self.app_cache[app_name] = after_effects_path
                return after_effects_path
            
        # Check for WhatsApp specifically
        if "whatsapp" in app_name.lower():
            whatsapp_paths = [
                os.path.join(os.environ['LOCALAPPDATA'], 'WhatsApp', 'WhatsApp.exe'),
                os.path.join(os.environ['PROGRAMFILES'], 'WindowsApps', 'WhatsAppDesktop_*', 'WhatsApp.exe'),
                os.path.join(os.environ['PROGRAMFILES(X86)'], 'WindowsApps', 'WhatsAppDesktop_*', 'WhatsApp.exe')
            ]
            for path in whatsapp_paths:
                if '*' in path:
                    # Handle wildcard paths
                    directory = os.path.dirname(path)
                    if os.path.exists(directory):
                        for item in os.listdir(directory):
                            if 'WhatsAppDesktop' in item:
                                full_path = os.path.join(directory, item, 'WhatsApp.exe')
                                if os.path.exists(full_path):
                                    self.app_cache[app_name] = full_path
                                    return full_path
                elif os.path.exists(path):
                    self.app_cache[app_name] = path
                    return path
                
        # Check for valorant specifically
        if "valorant" in app_name.lower():
            valorant_path = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Riot Games\VALORANT.lnk"
            if os.path.exists(valorant_path):
                self.app_cache[app_name] = valorant_path
                return valorant_path

        # Check for Spotify specifically
        if "spotify" in app_name.lower():
            spotify_paths = [
                os.path.join(os.environ['APPDATA'], 'Spotify', 'Spotify.exe'),
                "C:\\Program Files\\WindowsApps\\SpotifyAB.SpotifyMusic_1.1.0.0_x86__zpdnekdrzrea0\\Spotify.exe"
            ]
            for path in spotify_paths:
                if os.path.exists(path):
                    self.app_cache[app_name] = path
                    return path

        # Search in common installation directories
        common_dirs = [
            os.environ.get('ProgramFiles'),
            os.environ.get('ProgramFiles(x86)'),
            os.environ.get('LOCALAPPDATA'),
            os.path.join(os.environ.get('LOCALAPPDATA'), 'Programs')
        ]

        for dir in common_dirs:
            if dir:
                for root, _, files in os.walk(dir):
                    for file in files:
                        if file.lower().endswith('.exe') and app_name.lower() in file.lower():
                            app_path = os.path.join(root, file)
                            self.app_cache[app_name] = app_path
                            return app_path

        return None

    def execute_command(self, command):
        command = command.lower().strip()
        open_actions = ['open', 'start', 'run', 'launch']
        close_actions = ['close', 'terminate', 'exit', 'quit']

        for action in open_actions:
            if action in command:
                app_name = command.split(action, 1)[1].strip()
                if app_name:
                    return self.open_application(app_name)
                return "Which application would you like me to open?"

        for action in close_actions:
            if action in command:
                app_name = command.split(action, 1)[1].strip()
                if app_name:
                    return self.close_application(app_name)
                return "Which application would you like me to close?"

        if command.startswith('play '):
            return self.play_spotify_song(command[5:].strip())

        return "Sorry, I didn't understand that command. Try saying 'open notepad' or 'close chrome'."

    def open_application(self, app_name):
        app_path = self.find_app(app_name)
        if app_path:
            try:
                subprocess.Popen(app_path, shell=True)
                if app_name.lower() == 'spotify':
                    return self.handle_spotify_open()
                return f"Opening {app_name}."
            except Exception as e:
                return f"Sorry, I couldn't open {app_name}. Error: {str(e)}"
        return f"Sorry, I couldn't find {app_name}."

    def handle_spotify_open(self):
        speak("Spotify opened. Would you like to play a song?")
        response = self.listen()
        if response and 'yes' in response.lower():
            speak("What song would you like to play?")
            song_choice = self.listen()
            if song_choice:
                return self.play_spotify_song(song_choice)
            else:
                return "Sorry, I didn't catch the song name."
        return "Okay, let me know if you want to play music later."

    def play_spotify_song(self, song_choice):
        if not self.spotify:
            self.initialize_spotify()
        try:
            results = self.spotify.search(q=song_choice, type='track', limit=1)
            if results['tracks']['items']:
                track_uri = results['tracks']['items'][0]['uri']
                self.spotify.start_playback(uris=[track_uri])
                return f"Playing '{results['tracks']['items'][0]['name']}' on Spotify."
            else:
                return f"Sorry, I couldn't find the song '{song_choice}' on Spotify."
        except Exception as e:
            return f"Error playing song on Spotify: {str(e)}"

    def close_application(self, app_name):
        closed = False
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                proc_name = proc.info['name'].lower()
                proc_exe = proc.info['exe'].lower() if proc.info['exe'] else ''
                if app_name.lower() in proc_name or app_name.lower() in proc_exe:
                    proc.terminate()
                    proc.wait(timeout=5)  # Wait for the process to terminate
                    closed = True
                    print(f"Closed {proc_name}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception as e:
                print(f"Error closing {app_name}: {str(e)}")
        
        if closed:
            return f"Closed {app_name}."
        else:
            return f"Sorry, I couldn't find a running process for {app_name}."

    def listen(self):
        try:
            with self.mic as source:
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
        except sr.WaitTimeoutError:
            print("Listening timed out. No speech detected.")
            return None
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand that.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None

# Example usage
if __name__ == "__main__":
    ava = apps()
    
    speak("Hello! I am AVA. How can I assist you?")
    
    while True:
        speak("What would you like me to do?")
        user_input = ava.listen()
        if user_input:
            if 'quit' in user_input.lower():
                speak("Goodbye!")
                break
            else:
                response = ava.execute_command(user_input)
                speak(response)
        else:
            speak("I'm sorry, I didn't catch that. Could you please repeat?")
