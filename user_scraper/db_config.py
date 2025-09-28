import os
from pymongo import MongoClient
from datetime import datetime

class MongoDBHandler:
    def __init__(self, mongo_uri, database_name, collection_name):
        """Initialize MongoDB connection"""
        # Use provided parameters or fall back to environment variables or defaults
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.collection_name = collection_name
        
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            print(f"Connected to MongoDB: {self.database_name}.{self.collection_name}")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    def insert_user(self, user_data):
        """Insert a single user document"""
        try:
            # Add timestamp for when the record was scraped
            user_data['scraped_at'] = datetime.utcnow()
            
            # Create unique identifier to avoid duplicates
            filter_dict = {
                'user_id': user_data.get('user_id'),
                'group_id': user_data.get('group_id')
            }
            
            # Update if exists, insert if not (upsert)
            result = self.collection.update_one(
                filter_dict,
                {'$set': user_data},
                upsert=True
            )
            
            if result.upserted_id:
                print(f"Inserted new user: {user_data.get('username', 'N/A')} from group: {user_data.get('group', 'N/A')}")
            else:
                print(f"Updated existing user: {user_data.get('username', 'N/A')} from group: {user_data.get('group', 'N/A')}")
                
        except Exception as e:
            print(f"Error inserting user data: {e}")

    def insert_users_batch(self, users_list):
        """Insert multiple users at once for better performance"""
        try:
            if not users_list:
                return
                
            # Add timestamp to all records
            for user in users_list:
                user['scraped_at'] = datetime.utcnow()
            
            # Use bulk operations for better performance
            from pymongo import UpdateOne
            
            bulk_operations = []
            for user_data in users_list:
                filter_dict = {
                    'user_id': user_data.get('user_id'),
                    'group_id': user_data.get('group_id')
                }
                bulk_operations.append(
                    UpdateOne(filter_dict, {'$set': user_data}, upsert=True)
                )
            
            if bulk_operations:
                result = self.collection.bulk_write(bulk_operations)
                print(f"Processed {len(users_list)} users: {result.upserted_count} new, {result.modified_count} updated")
                
        except Exception as e:
            print(f"Error in batch insert: {e}")

    def get_users_by_group(self, group_id):
        """Retrieve all users from a specific group"""
        try:
            return list(self.collection.find({'group_id': group_id}))
        except Exception as e:
            print(f"Error retrieving users: {e}")
            return []

    def get_all_users(self):
        """Retrieve all scraped users"""
        try:
            return list(self.collection.find())
        except Exception as e:
            print(f"Error retrieving all users: {e}")
            return []

    def close_connection(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")