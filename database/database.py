import asyncio
import json
import os
from typing import Dict, List
from config import DB_URI, DB_NAME

class SimpleDatabase:
    """Simple file-based database for development/testing"""
    
    def __init__(self):
        self.users_file = "users.json"
        self.files_file = "files.json"
        self.users_data = self._load_data(self.users_file)
        self.files_data = self._load_data(self.files_file)
        print("✅ Simple Database initialized")
    
    def _load_data(self, filename: str) -> Dict:
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}
    
    def _save_data(self, filename: str, data: Dict):
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving {filename}: {e}")
    
    async def add_user(self, user_id: int, first_name: str = None):
        user_id_str = str(user_id)
        if user_id_str not in self.users_data:
            self.users_data[user_id_str] = {
                "user_id": user_id,
                "first_name": first_name,
                "join_date": "recent",
                "files_count": 0
            }
            self._save_data(self.users_file, self.users_data)
            print(f"✅ User {user_id} added")
    
    async def get_user(self, user_id: int):
        return self.users_data.get(str(user_id))
    
    async def is_user_exist(self, user_id: int) -> bool:
        return str(user_id) in self.users_data
    
    async def total_users_count(self) -> int:
        return len(self.users_data)
    
    async def add_file(self, file_id: int, user_id: int, chat_id: int = None):
        file_key = f"{user_id}_{file_id}"
        self.files_data[file_key] = {
            "file_id": file_id,
            "user_id": user_id,
            "chat_id": chat_id or user_id,
            "upload_date": "recent"
        }
        if str(user_id) in self.users_data:
            self.users_data[str(user_id)]["files_count"] += 1
            self._save_data(self.users_file, self.users_data)
        self._save_data(self.files_file, self.files_data)
    
    async def get_file(self, file_id: int):
        for file_data in self.files_data.values():
            if file_data.get("file_id") == file_id:
                return file_data
        return None
    
    async def total_files_count(self) -> int:
        return len(self.files_data)
    
    async def get_all_users(self) -> List[int]:
        return [int(uid) for uid in self.users_data.keys()]

try:
    import motor.motor_asyncio
    
    class MongoDatabase:
        def __init__(self):
            self.client = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
            self.db = self.client[DB_NAME]
            self.users = self.db.users
            self.files = self.db.files
            print("✅ MongoDB connected")
        
        async def add_user(self, user_id, first_name=None):
            await self.users.update_one(
                {"user_id": user_id},
                {"$setOnInsert": {"user_id": user_id, "first_name": first_name}},
                upsert=True
            )
        
        async def get_user(self, user_id):
            return await self.users.find_one({"user_id": user_id})
        
        async def is_user_exist(self, user_id):
            return await self.get_user(user_id) is not None
        
        async def total_users_count(self):
            return await self.users.count_documents({})
        
        async def add_file(self, file_id, user_id, chat_id=None):
            await self.files.update_one(
                {"_id": f"{user_id}_{file_id}"},
                {"$set": {
                    "file_id": file_id,
                    "user_id": user_id,
                    "chat_id": chat_id or user_id
                }},
                upsert=True
            )
        
        async def get_file(self, file_id):
            return await self.files.find_one({"file_id": file_id})
        
        async def total_files_count(self):
            return await self.files.count_documents({})
        
        async def get_all_users(self):
            return [u["user_id"] async for u in self.users.find({})]

    db = MongoDatabase()
except ImportError:
    db = SimpleDatabase()
