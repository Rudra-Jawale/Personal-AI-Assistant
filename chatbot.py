import os
from datetime import datetime

import google.genai as genai
from gemini_config import get_gemini_settings

# genai.configure(api_key=os.getenv("GOOGLE_GEMINI_KEY"))

AVA_SYSTEM_PROMPT = """You are AVA, an advanced personal AI voice assistant.
You are intelligent, warm, helpful, and confident — like a trusted companion who can do real tasks.

Rules:
- Keep responses SHORT (1-3 sentences max) because they will be spoken aloud via text-to-speech.
- Be natural and friendly, with the direct conversational style of a modern chat assistant.
- Do not use a user's name unless they explicitly use or request it in the current conversation.
- Answer the request directly. Do not automatically add a follow-up question, offer more help, or repeat a closing phrase after every reply.
- Be helpful with questions, explanations, advice, jokes, and casual conversation.
- If you don't know something, say so honestly and offer to search the web.
- Never use markdown, bullet points, or emojis — plain spoken English only.
- You can control apps, search the web, and summarize topics when the user asks explicitly.
"""


class AvaBrain:
    def __init__(self, memory_system=None, model=None):
        self.api_key, configured_model = get_gemini_settings()
        self.model = model or configured_model
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
        self.memory = memory_system
        self.session_history = []
        self.max_history = 12
        self._chat = None

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
                "Please add your GOOGLE_GEMINI_KEY to the .env file."
            )

        context = self._build_context()
        mood_note = ""
        if sentiment == "negative":
            mood_note = "The user seems upset — be empathetic and supportive."
        elif sentiment == "positive":
            mood_note = "The user seems in good spirits — match their energy lightly."

        prompt_parts = [AVA_SYSTEM_PROMPT]
        if context:
            prompt_parts.append(f"Context:\n{context}")
        if mood_note:
            prompt_parts.append(mood_note)
        prompt_parts.append(f"User: {user_message}")
        prompt = "\n\n".join(prompt_parts)

        try:
            if self._chat is None:
                self._chat = self.client.chats.create(model=self.model)

            response = self._chat.send_message(
                prompt,
                config={"max_output_tokens": 200, "temperature": 0.7},
            )
            reply = getattr(response, "text", "") or ""
            reply = reply.strip()
            if not reply and hasattr(response, "json"):
                reply = response.json().get("text", "").strip()

            if reply:
                self.session_history.append({"role": "user", "content": user_message})
                self.session_history.append({"role": "assistant", "content": reply})
                self._trim_history()
                return reply
            return "I couldn't generate a response from Gemini."
        except Exception as exc:
            return f"Something went wrong: {exc}"
        # except RateLimitError:
        #     return "I'm hitting API rate limits. Please check your OpenAI billing or try again shortly."
        # except APIConnectionError:
        #     return "I can't connect to my AI service right now. Please check your internet connection."
        # except APIError as exc:
        #     return f"I encountered an API error: {exc.message if hasattr(exc, 'message') else str(exc)}"
        # except Exception as exc:
        #     return f"Something went wrong: {exc}"

    def clear_session(self):
        self.session_history = []
        self._chat = None
