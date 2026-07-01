import speech_recognition as sr
from mtranslate import translate
from colorama import Fore, init

# Initialize colorama for colored output in terminal
init(autoreset=True)  # Automatically reset style

def listen_and_translate():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 2500
    recognizer.pause_threshold = 0.7

    # Step 1: Speech Recognition
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print(Fore.LIGHTGREEN_EX + "Listening... Please speak something in Hindi.")
        try:
            audio = recognizer.listen(source, timeout=None)
            print(Fore.YELLOW + "Processing audio...")
            recognized_txt = recognizer.recognize_google(audio, language="hi-IN").lower()
            print(Fore.CYAN + "Recognized Speech:", recognized_txt)  # Output recognized text

            # Step 2: Translation
            if recognized_txt:
                try:
                    translated_txt = translate(recognized_txt, to_language="en")
                    print(Fore.BLUE + "Translated Text:", translated_txt)
                    return translated_txt
                except Exception as e:
                    print(Fore.RED + "Translation Error:", e)
                    return ""
            else:
                print(Fore.RED + "No speech recognized.")
                return ""
        
        except sr.UnknownValueError:
            print(Fore.RED + "Could not understand the audio.")
            return ""
        except Exception as e:
            print(Fore.RED + "Recognition Error:", e)
            return ""
        