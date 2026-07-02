# web_search.py
import subprocess
import webbrowser
import os

class WebSearchAssistant:
    def __init__(self):
        self.chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
        if os.path.exists(self.chrome_path):
            webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(self.chrome_path))
            self.browser = 'chrome'
        else:
            self.browser = None

    def search_on_web(self, query):
        """Open Chrome and search for the given query on Google or specific websites."""
        if "youtube" in query:
            url = f"https://www.youtube.com/results?search_query={query.replace('youtube', '').strip()}"
        elif "instagram" in query:
            url = f"https://www.instagram.com/explore/tags/{query.replace('instagram', '').strip()}/"
        elif "facebook" in query:
            url = f"https://www.facebook.com/search/top/?q={query.replace('facebook', '').strip()}"
        else:
            url = f"https://www.google.com/search?q={query}"

        try:
            if self.browser:
                webbrowser.get(self.browser).open(url)
            else:
                webbrowser.open(url)
            return f"Searching for '{query}' on the web."
        except Exception as e:
            try:
                subprocess.Popen([self.chrome_path, url])
                return f"Searching for '{query}' on the web."
            except Exception as e:
                return f"Unable to open the browser. Error: {str(e)}"