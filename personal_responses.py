import json

def load_responses():
    try:
        with open('responses.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: responses.json not found")
        return {}

responses = load_responses()

def get_personal_response(command):
    return responses.get(command, "I'm not sure how to help with that.")