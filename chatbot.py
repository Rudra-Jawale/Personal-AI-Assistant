import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APIError, RateLimitError

load_dotenv()

AVA_SYSTEM_PROMPT = """You are AVA, an advanced personal AI voice assistant.
You are intelligent, warm, helpful, and confident — like a trusted companion who can do real tasks.

Rules:
- Keep responses SHORT (1-3 sentences max) because they will be spoken aloud via text-to-speech.
- Be natural and friendly. You may address the user by name if you know it.
- Be helpful with questions, explanations, advice, jokes, and casual conversation.
- If you don't know something, say so honestly and offer to search the web.
- Never use markdown, bullet points, or emojis — plain spoken English only.
- You can control apps, search the web, and summarize topics when the user asks explicitly.
"""


class AvaBrain:
    def __init__(self, memory_system=None, model=None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.memory = memory_system
        self.session_history = []
        self.max_history = 12

    def _build_context(self):
        parts = []

        now = datetime.now()
        parts.append(f"Current date and time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}.")

        if self.memory:
            personal = self.memory.memory.get("personal_info", {})
            if personal:
                facts = ", ".join(f"{k}: {v}" for k, v in personal.items())
                parts.append(f"Known personal info: {facts}.")

            learned = self.memory.get_learned_facts("user_facts")
            if learned:
                parts.append(f"Remembered facts: {'; '.join(learned[-10:])}.")

            recent = self.memory.get_recent_conversations(5)
            if recent:
                snippets = []
                for entry in recent:
                    snippets.append(
                        f"User: {entry['user_input']} | AVA: {entry['ava_response']}"
                    )
                parts.append("Recent conversation:\n" + "\n".join(snippets))

        return "\n".join(parts)

    def _trim_history(self):
        if len(self.session_history) > self.max_history:
            self.session_history = self.session_history[-self.max_history :]

    def chat(self, user_message, sentiment=None):
        if not self.client:
            return (
                "My AI core isn't configured yet. "
                "Please add your OPENAI_API_KEY to the .env file."
            )

        context = self._build_context()
        mood_note = ""
        if sentiment == "negative":
            mood_note = "The user seems upset — be empathetic and supportive."
        elif sentiment == "positive":
            mood_note = "The user seems in good spirits — match their energy lightly."

        messages = [{"role": "system", "content": AVA_SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})
        if mood_note:
            messages.append({"role": "system", "content": mood_note})

        messages.extend(self.session_history)
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.7,
            )
            reply = response.choices[0].message.content.strip()

            self.session_history.append({"role": "user", "content": user_message})
            self.session_history.append({"role": "assistant", "content": reply})
            self._trim_history()

            return reply

        except RateLimitError:
            return "I'm hitting API rate limits. Please check your OpenAI billing or try again shortly."
        except APIConnectionError:
            return "I can't connect to my AI service right now. Please check your internet connection."
        except APIError as exc:
            return f"I encountered an API error: {exc.message if hasattr(exc, 'message') else str(exc)}"
        except Exception as exc:
            return f"Something went wrong: {exc}"

    def clear_session(self):
        self.session_history = []
