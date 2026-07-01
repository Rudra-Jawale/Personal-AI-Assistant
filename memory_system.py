# memory_system.py

import json
from datetime import datetime
import os

class MemorySystem:
    def __init__(self, user_id):
        self.user_id = user_id
        self.memory_file = "memory.json"
        self.memory = self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                all_memory = json.load(f)
                return all_memory.get(self.user_id, self.create_default_memory())
        else:
            return self.create_default_memory()

    def create_default_memory(self):
        return {
            "personal_info": {},
            "preferences": {},
            "important_dates": {},
            "conversation_history": [],
            "learned_facts": {}
        }

    def save_memory(self):
        all_memory = {}
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                all_memory = json.load(f)
        all_memory[self.user_id] = self.memory
        with open(self.memory_file, 'w') as f:
            json.dump(all_memory, f, indent=4)

    def add_personal_info(self, key, value):
        self.memory["personal_info"][key] = value
        self.save_memory()

    def get_personal_info(self, key):
        return self.memory["personal_info"].get(key)

    def add_preference(self, category, preference):
        if category not in self.memory["preferences"]:
            self.memory["preferences"][category] = []
        self.memory["preferences"][category].append(preference)
        self.save_memory()

    def get_preferences(self, category):
        return self.memory["preferences"].get(category, [])

    def add_important_date(self, event, date):
        self.memory["important_dates"][event] = date
        self.save_memory()

    def get_important_dates(self):
        return self.memory["important_dates"]

    def add_conversation(self, user_input, ava_response):
        timestamp = datetime.now().isoformat()
        self.memory["conversation_history"].append({
            "timestamp": timestamp,
            "user_input": user_input,
            "ava_response": ava_response
        })
        if len(self.memory["conversation_history"]) > 100:  # Keep only last 100 conversations
            self.memory["conversation_history"] = self.memory["conversation_history"][-100:]
        self.save_memory()

    def get_recent_conversations(self, n=5):
        return self.memory["conversation_history"][-n:]

    def add_learned_fact(self, category, fact):
        if category not in self.memory["learned_facts"]:
            self.memory["learned_facts"][category] = []
        self.memory["learned_facts"][category].append(fact)
        self.save_memory()

    def get_learned_facts(self, category):
        return self.memory["learned_facts"].get(category, [])

    def search_memory(self, query):
        results = []
        for category, facts in self.memory["learned_facts"].items():
            for fact in facts:
                if query.lower() in fact.lower():
                    results.append((category, fact))
        return results

# Example usage
if __name__ == "__main__":
    memory = MemorySystem("user123")
    
    # Add personal info
    memory.add_personal_info("name", "John Doe")
    memory.add_personal_info("birthday", "1990-01-01")
    
    # Add preferences
    memory.add_preference("music", "rock")
    memory.add_preference("food", "pizza")
    
    # Add important date
    memory.add_important_date("Anniversary", "2022-06-15")
    
    # Add conversation
    memory.add_conversation("What's the weather like?", "It's sunny today.")
    
    # Add learned fact
    memory.add_learned_fact("science", "The Earth revolves around the Sun.")
    
    # Retrieve information
    print(f"Name: {memory.get_personal_info('name')}")
    print(f"Music preferences: {memory.get_preferences('music')}")
    print(f"Important dates: {memory.get_important_dates()}")
    print(f"Recent conversations: {memory.get_recent_conversations()}")
    print(f"Learned facts about science: {memory.get_learned_facts('science')}")
    
    # Search memory
    print(f"Search results for 'Sun': {memory.search_memory('Sun')}")