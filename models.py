from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    """
    Defines the structure for the incoming POST request body for search operations.
    """
    query: str


class Book(BaseModel):
    """
    Defines the structure for a single book result
    """
    title: str
    author: str
    published_year: Optional[str]
    subject: str

class BookItem(BaseModel):
    title: str
    author: str
    description: str

class SearchResponse(BaseModel):
    """
    Defines the structure for the incoming POST response body for search operations.
    """
    greeting: str
    books: List[BookItem]
    conclusion: str