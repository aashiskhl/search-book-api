import os
import json
import requests

def load_bad_words():
    try:
        url = os.getenv('BADWORDSOURCE')
        r = requests.get(url)
        r.raise_for_status()
        return [word for word in r.text.strip().split('\n') if word.lower() not in {"crime", "crimes"}]
    except Exception as e:
        print(f"Error loading bad words: {e}")
        return []

def search_open_library(search_terms: str, limit: int = 5):
    params = {
        "q": search_terms,
        "lang": "en",
        "limit": limit,
        "fields":"key,title,author_name,first_publish_year,subject",
    }
    try:
        url = os.getenv("OPEN_LIBRARY_API")
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        ### formating the result
        books_found = []
        for book in data.get("docs", []):
            books_found.append({
                "title": book.get("title", "n/a"),
                "author":", ".join(book.get("author_name", ["n/a"])),
                "published_year": book.get("first_publish_year", "n/a"),
                "subject": ", ".join(book.get("subject", ["n/a"])[:5]), # limit to first 5 subjects
            })
        return books_found
    except requests.RequestException as e:
        print(f"Error searching Open Library: {e}")
        raise

def first_prompt(original_query: str) -> str:
    return (
        "Extract up to 4 concise, space-separated keywords, genres, author names, or titles from the user query below, "
        "ignoring generic words (e.g., books, library, top, find, help, strong, small, big). "
        "Return only the keywords in a single space-separated string.\n\n"
        f"User query: {original_query}\nSearch Keywords:"
    )

def final_prompt(original_query: str, books_str: str) -> str:
    return (
        "You are a helpful librarian assistant for 'Book Search'.\n"
        f"User request: \"{original_query}\"\n"
        "Books found:\n"
        f"{books_str}\n\n"
        "Respond ONLY in this JSON format:\n"
        "{\n"
        '  "greeting": "<friendly greeting>",\n'
        '  "books": [\n'
        '    {\n'
        '      "title": "<book title>",\n'
        '      "author": "<author name>",\n'
        '      "description": "<one-sentence reason why this book matches the user\'s request>"\n'
        "    }\n"
        "    // ... more books\n"
        "  ],\n"
        '  "conclusion": "<engaging closing question or prompt>"\n'
        "}\n\n"
        "Instructions:\n"
        "- Use only the provided book data.\n"
        "- Do not invent details.\n"
        "- Keep descriptions brief and relevant.\n"
        "- Respond with valid JSON only."
    )

def parse_llm_response(raw_response):
    try:
        response = json.loads(raw_response)
        return response
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response: {e}")
        return {
            "greeting": "Sorry, there was an error processing the response.",
            "books": [],
            "conclusion": ""
        }

def normalize_search_term(search_term: str) -> str:
    words = search_term.lower().split()
    words = sorted(set(words))
    print("normalized term","-".join(words))
    return "-".join(words)