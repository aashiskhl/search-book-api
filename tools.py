import os
import requests

def load_bad_words():
    try:
        url = os.getenv('BADWORDSOURCE')
        r = requests.get(url)
        r.raise_for_status()
        return r.text.strip().split('\n')
    except Exception as e:
        print(f"Error loading bad words: {e}")
        return []



