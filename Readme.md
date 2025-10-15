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


Response Structure
The response is parsed into:
greeting: Friendly opening message.
books: Array of recommended books, each with:
title
author
description
conclusion: Closing question or prompt.

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