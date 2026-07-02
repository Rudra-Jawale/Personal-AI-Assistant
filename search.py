import os

import wikipedia
from colorama import Fore, init
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APIError, RateLimitError

from web_search import WebSearchAssistant
from sentiment_analysis import SentimentAnalyzer

load_dotenv()
init(autoreset=True)


class SummaryModule:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.web_search = WebSearchAssistant()
        self.sentiment_analyzer = SentimentAnalyzer()

    def get_wiki_summary(self, query):
        try:
            summary = wikipedia.summary(query, sentences=3)
            return {"source": "Wikipedia", "content": summary}
        except Exception:
            return None

    def get_chatgpt_summary(self, query):
        if not self.client:
            return None
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": "Provide a clear, concise spoken summary in 2-3 sentences. No markdown.",
                    },
                    {"role": "user", "content": f"Summarize: {query}"},
                ],
                max_tokens=300,
            )
            return {"source": "ChatGPT", "content": response.choices[0].message.content.strip()}
        except (RateLimitError, APIConnectionError, APIError) as exc:
            print(Fore.RED + f"ChatGPT Error: {exc}")
            return None

    def generate_summary(self, query):
        print(Fore.CYAN + f"Generating summary for: {query}")

        wiki_result = self.get_wiki_summary(query)
        if wiki_result:
            print(Fore.GREEN + "Found Wikipedia summary")
            return wiki_result

        chatgpt_result = self.get_chatgpt_summary(query)
        if chatgpt_result:
            print(Fore.GREEN + "Generated ChatGPT summary")
            return chatgpt_result

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
