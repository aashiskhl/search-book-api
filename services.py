import json
import os

import requests
from openai import OpenAI, OpenAIError

import tools


class LLMService:
    client = None
    profanity_words = None
    open_library_api = None

    def __init__(self):
        try:
            self.profanity_words = tools.load_bad_words()
            self.open_library_api = os.getenv("OPEN_LIBRARY_API")
            self.client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))
        except OpenAIError as e:
            print(f"Error initializing OpenAI client: {e}")
            raise e


    def check_for_profanity(self, query: str) -> bool:
        return any(word in self.profanity_words for word in query.lower().split())

    def get_search_terms_from_llm(self, query: str) -> str:
        if not self.client:
            raise ValueError("OpenAI client not initialized.")

        prompt = f"""
        Based on the following user query for a book, extract ONLY the most relevant keywords, genres, author names,
        or titles to use for a book search API. 
        Ignore generic keywords like books,library,top,find,help,etc.
        Return a concise, space-separated string of 1-4 keywords that would be most useful for a book search API.
        DO NOT include unnecessary words
        Return search terms that are more appropriate for open library search.
        Return these keywords in a single, space-separated string.
        
        User query: {query}
        Search Keywords:
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=50,
            )
            return response.choices[0].message.content.strip()
        except OpenAIError as e:
            print(f"Error generating search terms from LLM: {e}")
            raise e

    def search_open_library(self, search_terms: str, limit: int = 5):
        params = {
            "q": search_terms,
            "lang": "en",
            "limit": limit,
            "fields":"key,title,author_name,first_publish_year,subject",
        }
        try:
            url = self.open_library_api
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


    def generate_natural_language_response(self, original_query: str, books_data: list):
        if not self.client:
            raise ValueError("OpenAI client not initialized.")

        if not books_data:
            return "I am sorry, I could not find any books matching your query."

        books_str = "\n".join(
            [f"- Title: {b.get('title')}, Author:{b.get('author')}, Year:{b.get('published_year')}, Subjects: {b.get('subjects')}"
             for b in books_data]
        )
        prompt = f"""
        You are a friendly and helpful librarian assistant for a service called "Book Search". A user has searched for a book with the following request:
        "{original_query}"
        I have found the following books that might be a good match:
        {books_str}

        For each book listed above, include it in the "books" array in the JSON response, using only the provided information.

        Respond ONLY in the following JSON format:
        {{
          "greeting": "<friendly greeting>",
          "books": [
            {{
              "title": "<book title>",
              "author": "<author name>",
              "description": "<one-sentence reason why this book matches the user's request>"
            }}
            // ... more books
          ],
          "conclusion": "<engaging closing question or prompt>"
        }}

        Instructions:
        - Do not invent details not present in the provided data.
        - Only use the information provided.
        - Conclude with a question to encourage further interaction.
        - Keep descriptions brief and relevant.
        - Respond with valid JSON only.
        """

        try:
            response = self.client.chat.completions.create(
                model = "gpt-4o-mini",
                messages = [{"role": "user", "content": prompt}],
                temperature = 0.7,
                max_tokens = 500,
            )
            raw = response.choices[0].message.content
            print(raw)
            parsed = self.parse_llm_response(raw)
            return parsed
        except OpenAIError as e:
            print(f"Error generating natural language response: {e}")
            raise

    def parse_llm_response(self, raw_response):
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