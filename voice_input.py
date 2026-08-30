"""Microphone input for AVA — uses PyAudio when available, sounddevice on Python 3.14+."""

import time

import numpy as np
import speech_recognition as sr

try:
    import sounddevice as sd

    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    sd = None
    SOUNDDEVICE_AVAILABLE = False

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2


class VoiceListener:
    """Capture speech from the default microphone and return recognized text."""

    def __init__(self, calibrate=True):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3

        self.pyaudio_mic = None
        self.use_sounddevice = False

        try:
            self.pyaudio_mic = sr.Microphone(sample_rate=SAMPLE_RATE)
        except (AttributeError, OSError, LookupError):
            if SOUNDDEVICE_AVAILABLE:
                self.use_sounddevice = True
            else:
                print(
                    "Voice input unavailable: install PyAudio (Python <3.14) "
                    "or sounddevice for microphone support."
                )

        if calibrate and self.pyaudio_mic is not None:
            with self.pyaudio_mic as source:
                print("Calibrating for ambient noise... Please wait.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)

    @property
    def available(self):
        return self.pyaudio_mic is not None or self.use_sounddevice

    def _record_with_sounddevice(self, timeout=6, phrase_time_limit=12):
        block_duration = 0.1
        block_size = int(SAMPLE_RATE * block_duration)
        max_blocks = int(phrase_time_limit / block_duration)
        silence_blocks_needed = 12
        energy_threshold = 250

        recorded = []
        silence_count = 0
        started = False
        start_time = time.time()
        ambient_samples = []

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=block_size,
        ) as stream:
            for _ in range(max_blocks):
                if not started and time.time() - start_time > timeout:
                    raise sr.WaitTimeoutError()

                block, _ = stream.read(block_size)
                block = block.reshape(-1)
                energy = float(np.abs(block).mean())

                if not started and len(ambient_samples) < 10:
                    ambient_samples.append(energy)
                    if len(ambient_samples) == 10:
                        ambient = float(np.mean(ambient_samples))
                        energy_threshold = max(ambient * 1.8, 180)

                if energy > energy_threshold:
                    started = True
                    silence_count = 0
                    recorded.append(block.copy())
                elif started:
                    recorded.append(block.copy())
                    silence_count += 1
                    if silence_count >= silence_blocks_needed:
                        break

        if not recorded:
            raise sr.UnknownValueError()

        audio = np.concatenate(recorded)
        return sr.AudioData(audio.tobytes(), SAMPLE_RATE, SAMPLE_WIDTH)

    def listen(self, timeout=6, phrase_time_limit=12):
        if not self.available:
            print("Voice input is unavailable. Please type your command instead.")
            return None

        try:
            if self.pyaudio_mic is not None:
                with self.pyaudio_mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                    print("\nListening...")
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit,
                    )
            else:
                print("\nListening...")
                audio = self._record_with_sounddevice(timeout, phrase_time_limit)

            print("Processing speech...")
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.strip().lower()

        except sr.WaitTimeoutError:
            print("Listening timed out. Please try again.")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio. Please try again.")
            return None
        except sr.RequestError as exc:
            print(f"Speech recognition service error: {exc}")
            return None
        except Exception as exc:
            print(f"Error during listening: {exc}")
            return None
