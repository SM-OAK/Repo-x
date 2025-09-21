#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import motor.motor_asyncio
import pymongo
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.DB_URI)
        self.db = self.client[Config.DB_NAME]
        
        # Collections
        self.files = self.db.files
        self.users = self.db.users
        self.batches = self.db.batches
        self.settings = self.db.settings
        self.stats = self.db.stats
        
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Files collection indexes
            await self.files.create_index("file_id", unique=True)
            await self.files.create_index("uploaded_by")
            await self.files.create_index("upload_time")
            await self.files.create_index("batch_id")
            await self.files.create_index("file_type")
            
            # Users collection indexes
            await self.users.create_index("user_id", unique=True)
            await self.users.create_index("join_date")
            
            # Batches collection indexes
            await self.batches.create_index("batch_id", unique=True)
            await self.batches.create_index("created_by")
            await self.batches.create_index("created_at")
            
            logger.info("✅ Database indexes created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
    
    async def save_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Save or update user in database"""
        try:
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "last_active": datetime.now()
            }
            
            # Update existing user or create new one
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": user_data,
                    "$setOnInsert": {"join_date": datetime.now()}
                },
                upsert=True
            )
            
            return True
        except Exception as e:
            logger.error(f"Error saving user {user_id}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data from database"""
        try:
            return await self.users.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def save_file(self, file_data: Dict) -> bool:
        """Save file to database"""
        try:
            file_data["upload_time"] = datetime.now()
            await self.files.insert_one(file_data)
            return True
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False
    
    async def get_file(self, file_id: str) -> Optional[Dict]:
        """Get file from database"""
        try:
            return await self.files.find_one({"file_id": file_id})
        except Exception as e:
            logger.error(f"Error getting file {file_id}: {e}")
            return None
    
    async def get_files_by_user(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get files uploaded by a specific user"""
        try:
            cursor = self.files.find({"uploaded_by": user_id}).limit(limit).sort("upload_time", -1)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting files for user {user_id}: {e}")
            return []
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from database"""
        try:
            result = await self.files.delete_one({"file_id": file_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False
    
    async def save_batch(self, batch_data: Dict) -> bool:
        """Save batch information"""
        try:
            batch_data["created_at"] = datetime.now()
            await self.batches.insert_one(batch_data)
            return True
        except Exception as e:
            logger.error(f"Error saving batch: {e}")
            return False
    
    async def get_batch(self, batch_id: str) -> Optional[Dict]:
        """Get batch information"""
        try:
            return await self.batches.find_one({"batch_id": batch_id})
        except Exception as e:
            logger.error(f"Error getting batch {batch_id}: {e}")
            return None
    
    async def get_batch_files(self, batch_id: str) -> List[Dict]:
        """Get all files in a batch"""
        try:
            cursor = self.files.find({"batch_id": batch_id}).sort("upload_time", 1)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting batch files {batch_id}: {e}")
            return []
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        try:
            user_data = await self.get_user(user_id)
            if not user_data:
                return {"files_count": 0, "join_date": None, "total_size": 0}
            
            # Count files and calculate total size
            pipeline = [
                {"$match": {"uploaded_by": user_id}},
                {"$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "total_size": {"$sum": "$file_size"},
                    "types": {"$addToSet": "$file_type"}
                }}
            ]
            
            result = await self.files.aggregate(pipeline).to_list(length=1)
            
            if result:
                stats = result[0]
                return {
                    "files_count": stats["count"],
                    "total_size": stats["total_size"],
                    "file_types": stats["types"],
                    "join_date": user_data.get("join_date"),
                    "last_active": user_data.get("last_active")
                }
            else:
                return {
                    "files_count": 0,
                    "total_size": 0,
                    "file_types": [],
                    "join_date": user_data.get("join_date"),
                    "last_active": user_data.get("last_active")
                }
                
        except Exception as e:
            logger.error(f"Error getting user stats {user_id}: {e}")
            return {"files_count": 0, "join_date": None, "total_size": 0}
    
    async def get_global_stats(self) -> Dict:
        """Get global bot statistics"""
        try:
            total_users = await self.users.count_documents({})
            total_files = await self.files.count_documents({})
            total_batches = await self.batches.count_documents({})
            
            # Get total storage used
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total_size": {"$sum": "$file_size"}
                }}
            ]
            
            size_result = await self.files.aggregate(pipeline).to_list(length=1)
            total_size = size_result[0]["total_size"] if size_result else 0
            
            # Get file type distribution
            type_pipeline = [
                {"$group": {
                    "_id": "$file_type",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            
            type_result = await self.files.aggregate(type_pipeline).to_list(length=None)
            
            return {
                "total_users": total_users,
                "total_files": total_files,
                "total_batches": total_batches,
                "total_size": total_size,
                "file_types": type_result
            }
            
        except Exception as e:
            logger.error(f"Error getting global stats: {e}")
            return {
                "total_users": 0,
                "total_files": 0,
                "total_batches": 0,
                "total_size": 0,
                "file_types": []
            }
    
    async def get_recent_files(self, limit: int = 10) -> List[Dict]:
        """Get recently uploaded files"""
        try:
            cursor = self.files.find({}).limit(limit).sort("upload_time", -1)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting recent files: {e}")
            return []
    
    async def search_files(self, query: str, user_id: int = None, limit: int = 20) -> List[Dict]:
        """Search files by name"""
        try:
            search_filter = {"file_name": {"$regex": query, "$options": "i"}}
            if user_id:
                search_filter["uploaded_by"] = user_id
            
            cursor = self.files.find(search_filter).limit(limit).sort("upload_time", -1)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return []
    
    async def cleanup_old_files(self, days: int = 30) -> int:
        """Clean up files older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            result = await self.files.delete_many({"upload_time": {"$lt": cutoff_date}})
            logger.info(f"Cleaned up {result.deleted_count} old files")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return 0
    
    async def get_user_list(self, limit: int = 100, skip: int = 0) -> List[Dict]:
        """Get list of users (for admin purposes)"""
        try:
            cursor = self.users.find({}).limit(limit).skip(skip).sort("join_date", -1)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting user list: {e}")
            return []
    
    async def save_setting(self, key: str, value: Union[str, int, bool, Dict]) -> bool:
        """Save bot setting"""
        try:
            await self.settings.update_one(
                {"key": key},
                {"$set": {"key": key, "value": value, "updated_at": datetime.now()}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving setting {key}: {e}")
            return False
    
    async def get_setting(self, key: str, default=None):
        """Get bot setting"""
        try:
            setting = await self.settings.find_one({"key": key})
            return setting["value"] if setting else default
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default
    
    async def record_download(self, file_id: str, user_id: int, ip_address: str = None):
        """Record file download for analytics"""
        try:
            download_data = {
                "file_id": file_id,
                "user_id": user_id,
                "download_time": datetime.now(),
                "ip_address": ip_address
            }
            
            # Update file download count
            await self.files.update_one(
                {"file_id": file_id},
                {"$inc": {"download_count": 1}, "$push": {"downloads": download_data}}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error recording download: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        self.client.close()

# Create global database instance
db = Database()
