import asyncio
import os
import re
import subprocess
import sys
import tempfile

import edge_tts
import pyttsx3

try:
    import pygame
except ImportError:
    pygame = None

# Natural voice; AVA is pronounced "Ay-va" not "Ee-va"
VOICE = "en-US-AvaNeural"
AVA_PRONUNCIATION = "Ayva"


def prepare_speech_text(text):
    """Ensure AVA is spoken as Ay-va while keeping display text unchanged elsewhere."""
    return re.sub(r"\bAVA\b", AVA_PRONUNCIATION, text, flags=re.IGNORECASE)


async def generate_speech(text, filename):
    communicate = edge_tts.Communicate(prepare_speech_text(text), VOICE)
    await communicate.save(filename)


if pygame is not None:
    try:
        pygame.mixer.init()
    except pygame.error:
        pygame = None


def speak_with_pyttsx3(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.say(prepare_speech_text(text))
    engine.runAndWait()


def speak(text):
    if not text:
        return

    try:
        if pygame is None:
            speak_with_pyttsx3(text)
            return

        temp_file = os.path.join(tempfile.gettempdir(), "ava_voice.mp3")
        asyncio.run(generate_speech(text, temp_file))

        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()

        if os.path.exists(temp_file):
            os.remove(temp_file)

    except Exception as exc:
        print("Speech Error:", exc)
        try:
            speak_with_pyttsx3(text)
        except Exception:
            if sys.platform.startswith("win"):
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f'Add-Type -AssemblyName System.Speech; '
                        f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                        f'$s.Speak("{prepare_speech_text(text).replace(chr(34), chr(39))}")',
                    ],
                    check=False,
                )
