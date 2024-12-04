from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

try:
    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    
    # Test connection
    client.admin.command('ping')
    
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")