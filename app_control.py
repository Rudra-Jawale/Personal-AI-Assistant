import os
import re
import subprocess
import winreg

import psutil

from speak import speak

APP_ALIASES = {
    "chrome": "google chrome",
    "google": "google chrome",
    "firefox": "mozilla firefox",
    "edge": "microsoft edge",
    "vscode": "visual studio code",
    "vs code": "visual studio code",
    "word": "microsoft word",
    "excel": "microsoft excel",
    "powerpoint": "microsoft powerpoint",
    "ppt": "microsoft powerpoint",
    "cmd": "command prompt",
    "terminal": "windows terminal",
    "photos": "microsoft photos",
    "store": "microsoft store",
    "settings": "settings",
    "calc": "calculator",
    "file explorer": "file explorer",
    "explorer": "file explorer",
}


class apps:
    def __init__(self, voice_listener=None):
        self.app_cache = {}
        self.spotify = None
        self.voice = voice_listener

    def _normalize_name(self, app_name):
        cleaned = re.sub(r"[^a-z0-9\s]", " ", app_name.lower()).strip()
        cleaned = " ".join(cleaned.split())
        return APP_ALIASES.get(cleaned, cleaned)

    def _score_match(self, candidate, query):
        candidate = candidate.lower()
        query = query.lower()
        if candidate == query:
            return 100
        if candidate.startswith(query):
            return 90
        if query in candidate:
            return 75
        query_words = set(query.split())
        candidate_words = set(re.split(r"[\s\-_]+", candidate))
        overlap = len(query_words & candidate_words)
        if overlap:
            return 50 + overlap * 10
        return 0

    def _start_menu_roots(self):
        roots = []
        for env_key in ("ProgramData", "APPDATA"):
            base = os.environ.get(env_key)
            if base:
                roots.append(
                    os.path.join(base, "Microsoft", "Windows", "Start Menu", "Programs")
                )
        return [root for root in roots if os.path.isdir(root)]

    def _search_where(self, app_name):
        query = self._normalize_name(app_name)
        exe_name = query if query.endswith(".exe") else f"{query.split()[0]}.exe"
        try:
            result = subprocess.run(
                ["where", exe_name],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
            for line in result.stdout.splitlines():
                path = line.strip()
                if path and os.path.exists(path):
                    return path
        except (subprocess.SubprocessError, OSError):
            pass
        return None

    def _search_start_menu(self, app_name):
        query = self._normalize_name(app_name)
        best_path = None
        best_score = 0

        for root in self._start_menu_roots():
            for dirpath, _, filenames in os.walk(root):
                depth = dirpath[len(root) :].count(os.sep)
                if depth > 6:
                    continue
                for filename in filenames:
                    if not filename.lower().endswith((".lnk", ".url", ".exe")):
                        continue
                    name = os.path.splitext(filename)[0]
                    score = self._score_match(name, query)
                    if score > best_score:
                        best_score = score
                        best_path = os.path.join(dirpath, filename)
                        if score == 100:
                            return best_path

        return best_path if best_score >= 50 else None

    def _search_registry(self, app_name):
        query = self._normalize_name(app_name)
        best_path = None
        best_score = 0

        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(
                    hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
                ) as key:
                    index = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, index)
                            index += 1
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    exe_path, _ = winreg.QueryValueEx(subkey, "")
                                except OSError:
                                    continue
                                if not exe_path or not os.path.exists(exe_path):
                                    continue
                                candidate = os.path.splitext(subkey_name)[0]
                                score = self._score_match(candidate, query)
                                if score > best_score:
                                    best_score = score
                                    best_path = exe_path
                        except OSError:
                            break
            except OSError:
                continue

        return best_path if best_score >= 50 else None

    def _search_program_files(self, app_name):
        query = self._normalize_name(app_name)
        best_path = None
        best_score = 0
        search_roots = [
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
        ]

        for root in search_roots:
            if not root or not os.path.isdir(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                depth = dirpath[len(root) :].count(os.sep)
                if depth > 2:
                    continue
                for filename in filenames:
                    if not filename.lower().endswith(".exe"):
                        continue
                    candidate = os.path.splitext(filename)[0]
                    score = self._score_match(candidate, query)
                    if score > best_score:
                        best_score = score
                        best_path = os.path.join(dirpath, filename)

        return best_path if best_score >= 70 else None

    def _search_powershell_start_apps(self, app_name):
        query = self._normalize_name(app_name)
        ps_script = (
            "Get-StartApps | "
            f"Where-Object {{ $_.Name -like '*{query}*' }} | "
            "Select-Object -First 1 -ExpandProperty AppID"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            app_id = result.stdout.strip()
            if app_id:
                return f"shell:AppsFolder\\{app_id}"
        except (subprocess.SubprocessError, OSError):
            pass
        return None

    def find_app(self, app_name):
        if app_name in self.app_cache:
            return self.app_cache[app_name]

        search_name = self._normalize_name(app_name)
        finders = (
            self._search_start_menu,
            self._search_registry,
            self._search_where,
            self._search_powershell_start_apps,
            self._search_program_files,
        )

        for finder in finders:
            path = finder(search_name)
            if path:
                self.app_cache[app_name] = path
                return path

        return None

    def execute_command(self, command):
        command = command.lower().strip()
        open_actions = ("open", "start", "run", "launch")
        close_actions = ("close", "terminate", "exit", "quit")

        for action in open_actions:
            if f" {action} " in f" {command} " or command.startswith(f"{action} "):
                app_name = command.split(action, 1)[1].strip()
                if app_name:
                    return self.open_application(app_name)
                return "Which application would you like me to open?"

        for action in close_actions:
            if f" {action} " in f" {command} " or command.startswith(f"{action} "):
                app_name = command.split(action, 1)[1].strip()
                if app_name:
                    return self.close_application(app_name)
                return "Which application would you like me to close?"

        if command.startswith("play "):
            return self.play_spotify_song(command[5:].strip())

        return "Try saying open followed by any app name, or close followed by an app name."

    def open_application(self, app_name):
        display_name = app_name.strip()
        app_path = self.find_app(display_name)

        try:
            if app_path:
                os.startfile(app_path)
            else:
                subprocess.Popen(
                    f'start "" "{display_name}"',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            if display_name.lower() == "spotify":
                return self.handle_spotify_open()
            return f"Opening {display_name}."
        except OSError as exc:
            return f"Sorry, I couldn't open {display_name}. {exc}"

    def handle_spotify_open(self):
        if not self.voice or not self.voice.available:
            return "Spotify opened."

        speak("Spotify opened. Would you like to play a song?")
        response = self.voice.listen()
        if response and "yes" in response:
            speak("What song would you like to play?")
            song_choice = self.voice.listen()
            if song_choice:
                return self.play_spotify_song(song_choice)
            return "Sorry, I didn't catch the song name."
        return "Okay, let me know if you want to play music later."

    def initialize_spotify(self):
        if self.spotify:
            return
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyOAuth

            scope = "user-read-playback-state user-modify-playback-state"
            self.spotify = spotipy.Spotify(
                auth_manager=SpotifyOAuth(scope=scope, open_browser=False)
            )
        except Exception as exc:
            print(f"Spotify initialization failed: {exc}")

    def play_spotify_song(self, song_choice):
        self.initialize_spotify()
        if not self.spotify:
            return "Spotify is not configured on this device."
        try:
            results = self.spotify.search(q=song_choice, type="track", limit=1)
            tracks = results.get("tracks", {}).get("items", [])
            if tracks:
                track = tracks[0]
                self.spotify.start_playback(uris=[track["uri"]])
                return f"Playing {track['name']} on Spotify."
            return f"Sorry, I couldn't find {song_choice} on Spotify."
        except Exception as exc:
            return f"Error playing song on Spotify: {exc}"

    def close_application(self, app_name):
        query = self._normalize_name(app_name)
        closed = False

        for proc in psutil.process_iter(["name", "exe"]):
            try:
                proc_name = (proc.info["name"] or "").lower()
                proc_exe = (proc.info["exe"] or "").lower()
                if query in proc_name or query.replace(" ", "") in proc_name.replace(" ", ""):
                    proc.terminate()
                    proc.wait(timeout=5)
                    closed = True
                elif query in proc_exe:
                    proc.terminate()
                    proc.wait(timeout=5)
                    closed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except psutil.TimeoutExpired:
                closed = True

        if closed:
            return f"Closed {app_name}."
        return f"Sorry, I couldn't find a running process for {app_name}."
