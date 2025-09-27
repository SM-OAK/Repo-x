# database/database.py - Updated with chat_id support

import asyncio
import json
import os
from typing import Dict, List

class SimpleDatabase:
    """Simple file-based database for development/testing"""
    
    def __init__(self):
        self.users_file = "users.json"
        self.files_file = "files.json"
        self.users_data = self._load_data(self.users_file)
        self.files_data = self._load_data(self.files_file)
        print("✅ Simple Database initialized")
    
    def _load_data(self, filename: str) -> Dict:
        """Load data from JSON file"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}
    
    def _save_data(self, filename: str, data: Dict):
        """Save data to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving {filename}: {e}")
    
    async def add_user(self, user_id: int):
        """Add user to database"""
        try:
            user_id_str = str(user_id)
            if user_id_str not in self.users_data:
                self.users_data[user_id_str] = {
                    "user_id": user_id,
                    "join_date": "recent",
                    "files_count": 0
                }
                self._save_data(self.users_file, self.users_data)
                print(f"✅ User {user_id} added to database")
        except Exception as e:
            print(f"❌ Error adding user {user_id}: {e}")
    
    async def get_user(self, user_id: int):
        """Get user from database"""
        try:
            user_id_str = str(user_id)
            return self.users_data.get(user_id_str)
        except Exception as e:
            print(f"❌ Error getting user {user_id}: {e}")
            return None
    
    async def total_users_count(self) -> int:
        """Get total users count"""
        try:
            return len(self.users_data)
        except Exception as e:
            print(f"❌ Error counting users: {e}")
            return 0
    
    async def add_file(self, file_id: int, user_id: int, chat_id: int = None):
        """Add file to database with chat_id support"""
        try:
            file_key = f"{user_id}_{file_id}"
            self.files_data[file_key] = {
                "file_id": file_id,
                "user_id": user_id,
                "chat_id": chat_id or user_id,  # Use user_id as fallback
                "upload_date": "recent"
            }
            
            # Update user's file count
            user_id_str = str(user_id)
            if user_id_str in self.users_data:
                self.users_data[user_id_str]["files_count"] = self.users_data[user_id_str].get("files_count", 0) + 1
                self._save_data(self.users_file, self.users_data)
            
            self._save_data(self.files_file, self.files_data)
            print(f"✅ File {file_id} added for user {user_id} in chat {chat_id}")
        except Exception as e:
            print(f"❌ Error adding file {file_id}: {e}")
    
    async def get_file(self, file_id: int):
        """Get file from database"""
        try:
            for key, file_data in self.files_data.items():
                if file_data.get("file_id") == file_id:
                    return file_data
            return None
        except Exception as e:
            print(f"❌ Error getting file {file_id}: {e}")
            return None
    
    async def get_file_by_reference(self, chat_id: int, file_id: int):
        """Get file by chat_id and file_id combination"""
        try:
            for key, file_data in self.files_data.items():
                if (file_data.get("file_id") == file_id and 
                    file_data.get("chat_id") == chat_id):
                    return file_data
            return None
        except Exception as e:
            print(f"❌ Error getting file by reference: {e}")
            return None
    
    async def total_files_count(self) -> int:
        """Get total files count"""
        try:
            return len(self.files_data)
        except Exception as e:
            print(f"❌ Error counting files: {e}")
            return 0
    
    async def get_all_users(self) -> List[int]:
        """Get all users for broadcast"""
        try:
            return [int(user_id) for user_id in self.users_data.keys()]
        except Exception as e:
            print(f"❌ Error getting all users: {e}")
            return []

# Try to use MongoDB, fallback to simple database
try:
    import motor.motor_asyncio
    
    class MongoDatabase:
        """MongoDB Database Handler with chat_id support"""
        
        def __init__(self):
            try:
                from config import Config
                self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.DATABASE_URI)
                self.db = self.client[Config.DATABASE_NAME]
                self.users = self.db.users
                self.files = self.db.files
                print("✅ MongoDB Database connected")
            except Exception as e:
                print(f"❌ MongoDB connection failed: {e}")
                raise e
        
        async def add_user(self, user_id):
            try:
                user_data = {
                    "_id": user_id,
                    "user_id": user_id,
                    "join_date": None
                }
                await self.users.insert_one(user_data)
            except Exception:
                pass
        
        async def get_user(self, user_id):
            try:
                user = await self.users.find_one({"user_id": user_id})
                return user
            except Exception:
                return None
        
        async def total_users_count(self):
            try:
                count = await self.users.count_documents({})
                return count
            except Exception:
                return 0
        
        async def add_file(self, file_id, user_id, chat_id=None):
            try:
                file_data = {
                    "_id": f"{user_id}_{file_id}",
                    "file_id": file_id,
                    "user_id": user_id,
                    "chat_id": chat_id or user_id,
                    "upload_date": None
                }
                await self.files.insert_one(file_data)
            except Exception:
                pass
        
        async def get_file(self, file_id):
            try:
                file_data = await self.files.find_one({"file_id": file_id})
                return file_data
            except Exception:
                return None
        
        async def get_file_by_reference(self, chat_id, file_id):
            try:
                file_data = await self.files.find_one({
                    "file_id": file_id,
                    "chat_id": chat_id
                })
                return file_data
            except Exception:
                return None
        
        async def total_files_count(self):
            try:
                count = await self.files.count_documents({})
                return count
            except Exception:
                return 0
        
        async def get_all_users(self):
            try:
                users = []
                async for user in self.users.find({}):
                    users.append(user["user_id"])
                return users
            except Exception:
                return []
    
    # Try to initialize MongoDB
    try:
        db = MongoDatabase()
        print("✅ Using MongoDB Database")
    except Exception:
        db = SimpleDatabase()
        print("✅ Using Simple File Database (MongoDB not available)")
        
except ImportError:
    # Use simple database if motor is not available
    db = SimpleDatabase()
    print("✅ Using Simple File Database (motor not installed)")
