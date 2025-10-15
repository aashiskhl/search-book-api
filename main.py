import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from models import SearchResponse, SearchRequest, BookItem
from services import LLMService
from tool_service import ToolService

load_dotenv()

app = FastAPI()

llmservice = LLMService()
toolservice = ToolService()




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
            detail=f"Profanity detected in query. Profanity source: {os.getenv('BADWORDSOURCE')}",
        )

    try:
        response = llmservice.process_user_query(request.query)
        return SearchResponse(**response)
    except Exception as e:
        print(f"Error processing search request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing your request. Please try again later."
        )

@app.post("/searchs/tools", response_model=SearchResponse, tags=["Book Search (Fast)"])
async def search_books_fast(request: SearchRequest):
    if not toolservice:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM Service is not initialized. Check API keys."
        )
    query = request.query
    if toolservice.check_for_profanity(query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query contains inappropriate language. Please refine your request."
        )

    try:
        response_list = toolservice.process_query_with_tools(query)

        if not response_list:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The LLM returned an empty response. Please try a different query."
            )

        return response_list

    except HTTPException as e:
        print(f"An unexpected error occurred during processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your request."
        )
