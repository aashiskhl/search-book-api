import os
import utils
from google.cloud import firestore



class FirestoreService:
    fsClient = None
    def __init__(self):
        self.fsClient = firestore.Client()

    def get_response(self, search_term: str):
        doc_id = utils.normalize_search_term(search_term)
        doc_ref = self.fsClient.collection("book_search_cache").document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("response")
        return None

    def store_response(self, search_term: str, response: dict):
        doc_id = utils.normalize_search_term(search_term)
        doc_ref = self.fsClient.collection("book_search_cache").document(doc_id)
        doc_ref.set({"response": response})
