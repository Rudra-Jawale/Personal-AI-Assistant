# sentiment_analysis.py

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import colorama
from colorama import Fore, Style

# Download necessary NLTK data (run this once)
nltk.download('vader_lexicon', quiet=True)

class SentimentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        colorama.init(autoreset=True)

    def analyze(self, text):
        sentiment_scores = self.sia.polarity_scores(text)
        compound_score = sentiment_scores['compound']

        if compound_score >= 0.05:
            sentiment = "positive"
            color = Fore.GREEN
        elif compound_score <= -0.05:
            sentiment = "negative"
            color = Fore.RED
        else:
            sentiment = "neutral"
            color = Fore.YELLOW

        print(f"{color}Sentiment: {sentiment.capitalize()} (Score: {compound_score:.2f}){Style.RESET_ALL}")
        return sentiment, compound_score

    def get_response(self, sentiment, score):
        if sentiment == "positive":
            if score > 0.5:
                return "I'm glad you're feeling so positive! Is there anything specific that's making you happy?"
            else:
                return "That's good to hear. Is there anything I can do to help maintain that positive mood?"
        elif sentiment == "negative":
            if score < -0.5:
                return "I'm sorry to hear that you're feeling down. Would you like to talk about what's bothering you?"
            else:
                return "I sense that you might be feeling a bit low. Is there anything I can do to help cheer you up?"
        else:
            return "I see. Is there anything specific you'd like to discuss or any way I can assist you?"

# Example usage
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    while True:
        user_input = input("Enter some text (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
        
        sentiment, score = analyzer.analyze(user_input)
        response = analyzer.get_response(sentiment, score)
        print(f"AVA: {response}")