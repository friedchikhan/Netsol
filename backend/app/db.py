from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

try:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
    client.admin.command("ping")  
    print("✅ MongoDB connection successful.")
except ConnectionFailure:
    print("❌ MongoDB connection failed. Is the server running?")
    raise

db = client["netsoltask"]
chat_collection = db["huh"]