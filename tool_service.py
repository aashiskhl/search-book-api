import json
import os
import threading

import requests
import utils
from openai import OpenAI, OpenAIError
from firestore_service import FirestoreService

class ToolService:
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

    def check_for_profanity(self, query: str) -> bool:
        return any(word in self.profanity_words for word in query.lower().split())

    def search_open_library(self, search_terms: str) -> str:
        books_found = utils.search_open_library(search_terms, limit=5)

        if not books_found:
            result = json.dumps({"status": "No books found."})
        else:
            result = json.dumps(books_found)

        return result

    def process_query_with_tools(self, query: str):
        """
        leverages tools to process the user query.
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured.")

        tools_def = [
            {
                "type": "function",
                "function": {
                    "name": "search_open_library",
                    "description": "Searches for books based on keywords like title, author, or genre.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_terms": {
                                "type": "string",
                                "description": "The keywords to search for. e.g., 'dune frank herbert' or 'romance mystery female lead'.",
                            },
                        },
                        "required": ["search_terms"],
                    },
                },
            }
        ]

        messages = [{"role": "user", "content": utils.first_prompt(query)}]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools_def,
            tool_choice="required",
            temperature=0.2
        )
        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            function_name = response_message.tool_calls[0].function.name
            if function_name == "search_open_library":
                function_args = json.loads(response_message.tool_calls[0].function.arguments) #formatted search terms from LLM
                search_terms = function_args.get("search_terms")


                # check in firestore
                response = self.fsService.get_response(search_terms)
                if response:
                    return response

                function_response = self.search_open_library(search_terms=search_terms) ## pull books from open library
                messages.append(
                    {
                        "tool_call_id": response_message.tool_calls[0].id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )

                prompt = utils.final_prompt(
                    original_query=query,
                    books_str=function_response
                )
                second_messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ]

                final_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=second_messages,
                    temperature=0.7
                )
                raw_text = final_response.choices[0].message.content
                parsed = utils.parse_llm_response(raw_text)
                threading.Thread(
                    target=self.fsService.store_response,
                    args=(search_terms, parsed),
                    daemon=True
                ).start()
                return parsed

        return [response_message.content]

