# Book Search API

A FastAPI-based backend service for searching and recommending books. Designed to work with a frontend that parses structured responses for easy display.

## Features

- **POST /search-books**: Search for books by query and receive structured recommendations.
- CORS enabled for frontend integration.
- Responses are formatted for easy parsing: greeting, book list, and conclusion are separated.
- Each book item includes title, author, and a short description.

## Request Example

**Endpoint:** `/search-books`  
**Method:** `POST`  
**Request Body:**
```json
{
  "query": "thriller books"
}
```

## Response Structure
The response is parsed into:
- greeting: Friendly opening message.
- books: Array of recommended books, each with:
    - title: Book title.
    - author: Book author.
    - description: Short description of the book.
- conclusion: Closing question or prompt.

```json
{
  "greeting": "Here are some thrilling books you might enjoy:",
  "books": [
    {
      "title": "The Silent Patient",
      "author": "Alex Michaelides",
      "description": "A psychological thriller about a woman who stops speaking after a traumatic event."
    },
    ...
   ]
```

# Setup
1. Clone the repository
2. Install dependencies
   - ``pip install -r requirements.txt``
3. Run the server
   - ``uvicorn main:app --reload``
   


## CORS
1. CORS is enabled for all origins. 
2. For production, update allow_origins in `main.py` to restrict access.


### Project Structure
- `main.py`: FastAPI app and endpoints
- `services.py`: Book search and recommendation services that uses llm
- `models.py`: Pydantic models for request/response
- `tools.py`: Helper functions (e.g., response parsing)
- `requirements.txt`: Python dependencies


## LLM Selection and Service Setup

1. Generating search_terms: 
    - The initial LLM (e.g., OpenAI GPT-3.5-turbo) is used to analyze the user’s query and extract or generate relevant `search_terms`. 
    - This step leverages the LLM’s strong natural language understanding to interpret ambiguous or complex queries, ensuring the search is accurate and context-aware. 
    - `GPT-3.5-turbo` is chosen for its balance of speed, cost, and language comprehension.
2. Using search_terms: 
    - The extracted search_terms are then used to query `Open Library API` to retrieve a list of books that match the criteria.
    - The service sends an HTTP request (`requests.get`) to Open Library's search endpoint, passing the terms as query parameters.
    - The API returns a list of books matching the search criteria
    - This step is more about data retrieval and less about language generation, so it can be handled by a simpler, more cost-effective model or even a direct API call without an LLM.