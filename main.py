from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from models import SearchResponse, SearchRequest, BookItem
from services import LLMService

load_dotenv()

app = FastAPI()

llmservice = LLMService()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "This is a book search API service"}


@app.post("/sample", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def sample():
    return SearchResponse(
        greeting="Hello! Here are some books you might like:",
        books=[
            BookItem(
                title="The Great Gatsby",
                author="F. Scott Fitzgerald",
                description="A classic novel set in the Roaring Twenties."
            ),
            BookItem(
                title="To Kill a Mockingbird",
                author="Harper Lee",
                description="A novel about racial injustice in the Deep South."
            )
        ],
        conclusion="Let me know if you need more recommendations!"
    )


@app.post("/search-books", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_books(request: SearchRequest):
    """
    Search for books based on the user's query and return a natural language formatted response.

    This function processes the search query provided in the request by first checking
    the query for any profanity or inappropriate content. If the query is deemed appropriate,
    it generates search terms using a Language Learning Model (LLM) service, retrieves book
    data from an external resource, and prepares a natural language response based on the
    retrieved data.

    :param request: The search request containing the query string provided by the user,
        which will be processed and used to fetch related book data.
    :type request: SearchRequest
    :return: A structured search response containing a natural language processed result for
        the user's query.
    :rtype: SearchResponse
    :raises HTTPException: If the query contains profanity or inappropriate content, or if
        an unexpected error occurs during processing.
    """
    if llmservice.check_for_profanity(request.query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query contains profanity or other inappropriate content."
        )

    try:
        search_terms = llmservice.get_search_terms_from_llm(request.query)
        print("search term is: ", search_terms)
        books_data = llmservice.search_open_library(search_terms, limit=5)
        if not books_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No books found matching your query."
            )
        natural_response = llmservice.generate_natural_language_response(request.query, books_data)
        return SearchResponse(**natural_response)
    except Exception as e:
        print(f"Error processing search request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing your request. Please try again later."
        )




