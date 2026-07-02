import asyncio
import os
import subprocess
import sys
import edge_tts
import pyttsx3
import pygame
import tempfile
# try:
#     import winsound
# except ImportError:  # non-Windows environments
#     winsound = None

# Text-to-speech configuration
VOICE = "en-US-MichelleNeural"

pygame.mixer.init()

async def generate_speech(text, filename):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)


# def speak_text(text):
#     engine = pyttsx3.init()
#     engine.say(text)
#     engine.runAndWait()


# def play_audio(file_path):
#     if not os.path.exists(file_path):
#         print(f"Audio file not found: {file_path}")
#         return

#     file_path = os.path.abspath(file_path)
#     extension = os.path.splitext(file_path)[1].lower()

#     try:
#         if extension == ".wav" and winsound is not None:
#             winsound.PlaySound(file_path, winsound.SND_FILENAME)
#             return

#         if sys.platform.startswith("win"):
#             try:
#                 os.startfile(file_path)  # type: ignore[attr-defined]
#                 return
#             except Exception as exc:
#                 print(f"Fallback audio playback failed: {exc}")
#                 return

#         print(f"No compatible audio player available for {file_path}")
#     except Exception as exc:
#         print(f"Error during audio playback: {exc}")


# async def amain(TEXT, output_file) -> None:
#     try:
#         cm_txt = edge_tts.Communicate(TEXT, VOICE)
#         await cm_txt.save(output_file)
#         play_audio(output_file)
#     except Exception as exc:
#         print(f"Error in amain: {exc}")
#     finally:
#         remove_file(output_file)


# def remove_file(file_path):
#     if not file_path or not os.path.exists(file_path):
#         return

#     max_attempts = 3
#     attempts = 0
#     while attempts < max_attempts:
#         try:
#             os.remove(file_path)
#             break
#         except Exception as exc:
#             print(f"Error while removing file: {exc}")
#             attempts += 1


# def speak(TEXT, output_file=None):
#     if output_file is None:
#         output_file = os.path.join(os.getcwd(), "speaks.mp3")
#     asyncio.run(amain(TEXT, output_file))
def speak(text):
    try:
        temp_file = os.path.join(tempfile.gettempdir(), "ava_voice.mp3")

        asyncio.run(generate_speech(text, temp_file))

        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()

        if os.path.exists(temp_file):
            os.remove(temp_file)

    except Exception as e:
        print("Speech Error:", e)