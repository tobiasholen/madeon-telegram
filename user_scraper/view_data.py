#!/usr/bin/env python3
"""
MongoDB Data Viewer for Telegram Scraper
This script allows you to view and query the scraped users from MongoDB
"""

from dotenv import load_dotenv
import os
from db_config import MongoDBHandler

def main():
    # Load environment variables
    load_dotenv()
    
    try:
        # Get MongoDB configuration
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        database_name = os.getenv('MONGODB_DATABASE', 'telegram_scraper')
        collection_name = os.getenv('MONGODB_COLLECTION', 'scraped_users')
        
        # Initialize MongoDB connection
        db_handler = MongoDBHandler(mongo_uri, database_name, collection_name)
        
        print("=== MongoDB Data Viewer ===")
        print("1. View all users")
        print("2. View users by group")
        print("3. View statistics")
        print("4. Export to CSV")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            view_all_users(db_handler)
        elif choice == "2":
            view_users_by_group(db_handler)
        elif choice == "3":
            view_statistics(db_handler)
        elif choice == "4":
            export_to_csv(db_handler)
        else:
            print("Invalid choice!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'db_handler' in locals():
            db_handler.close_connection()

def view_all_users(db_handler):
    """Display all users in the database"""
    users = db_handler.get_all_users()
    
    if not users:
        print("No users found in the database.")
        return
    
    print(f"\n=== All Users ({len(users)} total) ===")
    for i, user in enumerate(users, 1):
        print(f"{i}. Username: {user.get('username', 'N/A')}")
        print(f"   Name: {user.get('first_name', '')} {user.get('last_name', '')}")
        print(f"   Phone: {user.get('phone', 'N/A')}")
        print(f"   Group: {user.get('group', 'N/A')}")
        print(f"   User ID: {user.get('user_id', 'N/A')}")
        print(f"   Scraped: {user.get('scraped_at', 'N/A')}")
        print("-" * 50)

def view_users_by_group(db_handler):
    """Display users filtered by group"""
    # First, get all unique groups
    pipeline = [
        {"$group": {"_id": "$group", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    groups = list(db_handler.collection.aggregate(pipeline))
    
    if not groups:
        print("No groups found in the database.")
        return
    
    print("\n=== Available Groups ===")
    for i, group in enumerate(groups, 1):
        print(f"{i}. {group['_id']} ({group['count']} users)")
    
    try:
        choice = int(input("\nEnter group number: ")) - 1
        if 0 <= choice < len(groups):
            selected_group = groups[choice]['_id']
            users = list(db_handler.collection.find({"group": selected_group}))
            
            print(f"\n=== Users in '{selected_group}' ({len(users)} users) ===")
            for i, user in enumerate(users, 1):
                print(f"{i}. Username: {user.get('username', 'N/A')}")
                print(f"   Name: {user.get('first_name', '')} {user.get('last_name', '')}")
                print(f"   Phone: {user.get('phone', 'N/A')}")
                print(f"   User ID: {user.get('user_id', 'N/A')}")
                print("-" * 30)
        else:
            print("Invalid group selection!")
    except ValueError:
        print("Invalid input! Please enter a number.")

def view_statistics(db_handler):
    """Display database statistics"""
    total_users = db_handler.collection.count_documents({})
    
    # Group statistics
    pipeline = [
        {"$group": {"_id": "$group", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    group_stats = list(db_handler.collection.aggregate(pipeline))
    
    # Users with phone numbers
    users_with_phone = db_handler.collection.count_documents({"phone": {"$ne": ""}})
    
    # Recent scraping activity (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_users = db_handler.collection.count_documents({"scraped_at": {"$gte": yesterday}})
    
    print("\n=== Database Statistics ===")
    print(f"Total Users: {total_users}")
    print(f"Users with Phone Numbers: {users_with_phone}")
    print(f"Users Scraped (Last 24h): {recent_users}")
    print(f"Total Groups: {len(group_stats)}")
    
    print(f"\n=== Top Groups by User Count ===")
    for group in group_stats[:10]:  # Top 10 groups
        print(f"- {group['_id']}: {group['count']} users")

def export_to_csv(db_handler):
    """Export data to CSV file"""
    import csv
    from datetime import datetime
    
    users = db_handler.get_all_users()
    
    if not users:
        print("No users found to export.")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"telegram_users_export_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['username', 'first_name', 'last_name', 'phone', 'group', 'user_id', 'group_id', 'scraped_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for user in users:
                # Convert ObjectId and datetime for CSV
                user_row = {}
                for field in fieldnames:
                    value = user.get(field, '')
                    if field == 'scraped_at' and value:
                        value = value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(value, 'strftime') else str(value)
                    user_row[field] = value
                writer.writerow(user_row)
        
        print(f"Data exported successfully to: {filename}")
        print(f"Total records exported: {len(users)}")
        
    except Exception as e:
        print(f"Error exporting to CSV: {e}")

if __name__ == "__main__":
    main()