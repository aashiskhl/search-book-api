import json
import os
import threading
import requests
from fastapi import HTTPException,status
from openai import OpenAI, OpenAIError

import utils
from firestore_service import FirestoreService


class LLMService:
    client = None
    profanity_words = None
    open_library_api = None
    fsService = None

    def __init__(self):
        try:
            self.fsService = FirestoreService()
            self.profanity_words = utils.load_bad_words()
            self.open_library_api = os.getenv("OPEN_LIBRARY_API")
            self.client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))
        except OpenAIError as e:
            print(f"Error initializing OpenAI client: {e}")
            raise e


    def process_user_query(self, query: str):
        search_terms = self.get_search_terms_from_llm(query)
        print("search term is: ", search_terms)

        # check in firestore
        response = self.fsService.get_response(search_terms)
        if response:
            return response


        books_data = utils.search_open_library(search_terms, limit=5)
        if not books_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No books found matching your query."
            )
        return self.generate_natural_language_response(query, books_data, search_terms)

    def check_for_profanity(self, query: str) -> bool:
        return any(word in self.profanity_words for word in query.lower().split())

    def get_search_terms_from_llm(self, query: str) -> str:
        if not self.client:
            raise ValueError("OpenAI client not initialized.")

        prompt = f"""
        Based on the following user query for a book, extract ONLY the most relevant keywords, genres, author names,
        or titles to use for a book search API. 
        IGNORE generic keywords like books,library,top,find,help,strong,small,big etc.
        ONLY GENERATE maximum of 4 keywords that are concise, space-separated that are more relevant for a book search API
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

    def generate_natural_language_response(self, original_query: str, books_data: list, search_terms: str):
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
            parsed = utils.parse_llm_response(raw)
            threading.Thread(
                target=self.fsService.store_response,
                args=(search_terms, parsed),
                daemon=True
            ).start()
            return parsed
        except OpenAIError as e:
            print(f"Error generating natural language response: {e}")
            raise




