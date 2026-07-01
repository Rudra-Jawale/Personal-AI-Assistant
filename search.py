import speech_recognition as sr
import pyttsx3
import openai
import os
from colorama import Fore, init
import wikipedia
from web_search import WebSearchAssistant
from sentiment_analysis import SentimentAnalyzer

# Initialize colorama for colored output
init(autoreset=True)

class SummaryModule:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.openai_api_key
        self.web_search = WebSearchAssistant()
        self.sentiment_analyzer = SentimentAnalyzer()

    def get_wiki_summary(self, query):
        """Get summary from Wikipedia"""
        try:
            summary = wikipedia.summary(query, sentences=3)
            return {"source": "Wikipedia", "content": summary}
        except Exception:
            return None

    def get_chatgpt_summary(self, query):
        """Get summary from ChatGPT"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Provide a clear and concise summary of the given topic."},
                    {"role": "user", "content": f"Please provide a comprehensive summary of: {query}"}
                ],
                max_tokens=300
            )
            return {"source": "ChatGPT", "content": response.choices[0].message['content'].strip()}
        except Exception as e:
            print(Fore.RED + f"ChatGPT Error: {str(e)}")
            return None

    def generate_summary(self, query):
        """Generate a comprehensive summary using multiple sources"""
        print(Fore.CYAN + f"Generating summary for: {query}")

        # First try Wikipedia
        wiki_result = self.get_wiki_summary(query)
        if wiki_result:
            print(Fore.GREEN + "Found Wikipedia summary")
            return wiki_result

        # If Wikipedia fails, try ChatGPT
        chatgpt_result = self.get_chatgpt_summary(query)
        if chatgpt_result:
            print(Fore.GREEN + "Generated ChatGPT summary")
            return chatgpt_result

        # If both fail, try web search
        try:
            web_result = self.web_search.search_on_web(query)
            if web_result:
                return {"source": "Web Search", "content": web_result}
        except Exception as e:
            print(Fore.RED + f"Web Search Error: {str(e)}")

        return {"source": "Error", "content": "Sorry, I couldn't generate a summary for that topic."}

    def process_summary_command(self, command):
        """Process the summary command and return appropriate response"""
        # Remove 'summary' from the command
        query = command.replace("summary", "", 1).strip()
        
        if not query:
            return "Please specify what you'd like a summary about."

        # Analyze sentiment of the query
        sentiment, _ = self.sentiment_analyzer.analyze(query)
        
        # Get the summary
        result = self.generate_summary(query)
        
        # Format the response
        response = f"Based on {result['source']}:\n{result['content']}"
        
        # Add sentiment-based response if appropriate
        if sentiment == "negative":
            response += "\nI notice this topic might be sensitive. Let me know if you'd like to discuss it further."
        
        return response

def create_summary_instance():
    """Factory function to create and return a SummaryModule instance"""
    return SummaryModule()

# Example usage (only if running directly)
if __name__ == "__main__":
    summary_module = SummaryModule()
    
    while True:
        try:
            command = input("Enter your query (or 'exit' to quit): ")
            if command.lower() == 'exit':
                break
            if command.lower().startswith('summary'):
                result = summary_module.process_summary_command(command)
                print(Fore.CYAN + "\nSummary Result:")
                print(Fore.WHITE + result)
            else:
                print(Fore.YELLOW + "Please start your query with 'summary'")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(Fore.RED + f"An error occurred: {str(e)}")