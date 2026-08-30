import os

import wikipedia
from colorama import Fore, init
import google.genai as genai
from gemini_config import get_gemini_settings

from web_search import WebSearchAssistant
from sentiment_analysis import SentimentAnalyzer

init(autoreset=True)


class SummaryModule:
    def __init__(self):
        self.api_key, self.model = get_gemini_settings()
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.web_search = WebSearchAssistant()
        self.sentiment_analyzer = SentimentAnalyzer()

    def get_wiki_summary(self, query):
        try:
            summary = wikipedia.summary(query, sentences=3)
            return {"source": "Wikipedia", "content": summary}
        except Exception:
            return None

    def get_gemini_summary(self, query):
        if not self.client:
            return None
        try:
            chat = self.client.chats.create(model=self.model)
            response = chat.send_message(
                f"Provide a clear, concise spoken summary in 2-3 sentences. No markdown.\n\nSummarize: {query}",
                config={"max_output_tokens": 300, "temperature": 0.3},
            )
            reply = getattr(response, "text", "") or ""
            return {"source": "Gemini", "content": reply.strip()}
        except Exception as exc:
            print(Fore.RED + f"Gemini Error: {exc}")
            return None

    def generate_summary(self, query):
        print(Fore.CYAN + f"Generating summary for: {query}")

        wiki_result = self.get_wiki_summary(query)
        if wiki_result:
            print(Fore.GREEN + "Found Wikipedia summary")
            return wiki_result

        gemini_result = self.get_gemini_summary(query)
        if gemini_result:
            print(Fore.GREEN + "Generated Gemini summary")
            return gemini_result

        try:
            web_result = self.web_search.search_on_web(query)
            if web_result:
                return {"source": "Web Search", "content": web_result}
        except Exception as exc:
            print(Fore.RED + f"Web Search Error: {exc}")

        return {"source": "Error", "content": "Sorry, I couldn't generate a summary for that topic."}

    def process_summary_command(self, command):
        query = command.replace("summary", "", 1).strip()

        if not query:
            return "Please specify what you'd like a summary about."

        sentiment, _ = self.sentiment_analyzer.analyze(query)
        result = self.generate_summary(query)
        response = f"Based on {result['source']}: {result['content']}"

        if sentiment == "negative":
            response += " I notice this topic might be sensitive. Let me know if you'd like to discuss it further."

        return response


def create_summary_instance():
    return SummaryModule()
