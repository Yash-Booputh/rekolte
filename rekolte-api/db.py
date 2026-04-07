from pymongo import MongoClient
from config import MONGODB_URI

_client = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
    return _client["rekolte"]
