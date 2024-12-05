from pymongo import MongoClient, DESCENDING
from typing import Dict, List, Optional
from datetime import datetime
import streamlit as st

class Database:
    def __init__(self):
        mongodb_uri = st.secrets["MONGODB_URI"]
        if not mongodb_uri:
            raise ValueError("MongoDB URI not found in secrets")
        
        self.client = MongoClient(mongodb_uri)
        self.db = self.client.github_contributions
        self.users = self.db.users
        
        # Create indexes
        self.users.create_index([("username", 1)], unique=True)
        self.users.create_index([("total_net", DESCENDING)])

    def store_user_stats(self, 
                        username: str, 
                        stats_all_time: Dict,
                        stats_2024: Dict,
                        avatar_url: Optional[str] = None) -> bool:
        """Store user statistics if they don't exist or update if changed"""
        
        doc = {
            "username": username,
            "all_time": {
                "total_added": stats_all_time["total_added"],
                "total_deleted": stats_all_time["total_deleted"],
                "total_net": stats_all_time["total_net"]
            },
            "year_2024": {
                "total_added": stats_2024["total_added"],
                "total_deleted": stats_2024["total_deleted"],
                "total_net": stats_2024["total_net"]
            },
            "avatar_url": avatar_url,
            "last_updated": datetime.utcnow()
        }
        
        try:
            self.users.update_one(
                {"username": username},
                {"$set": doc},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error storing user stats: {e}")
            return False

    def get_leaderboard(self, period: str = 'all_time', limit: int = 10) -> List[Dict]:
        """Get top contributors by net lines for a specific period"""
        sort_field = f"{period}.total_net"
        
        try:
            results = self.users.find(
                {},
                {
                    "username": 1,
                    f"{period}": 1,
                    "avatar_url": 1,
                    "_id": 0
                }
            ).sort(sort_field, DESCENDING).limit(limit)
            
            return list(results)
        except Exception as e:
            print(f"Error fetching leaderboard: {e}")
            return []

    def get_user_stats(self, username: str) -> Optional[Dict]:
        """Get stats for a specific user"""
        try:
            return self.users.find_one(
                {"username": username},
                {"_id": 0}
            )
        except Exception as e:
            print(f"Error fetching user stats: {e}")
            return None

    def search_users(self, query: str, limit: int = 5) -> list:
        """
        Search for users by exact username match
        
        Args:
            query (str): The exact username to search for
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of matching user stats
        """
        try:
            # Case-insensitive exact match search
            users = self.db.users.find(
                {"username": {"$regex": f"^{query}$", "$options": "i"}},
                {"_id": 0},  # Exclude MongoDB _id field
                limit=limit
            )
            return list(users)
        except Exception as e:
            print(f"Error searching users: {e}")
            return []