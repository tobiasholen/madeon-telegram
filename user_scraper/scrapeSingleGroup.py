from telethon import TelegramClient, sync
from dotenv import load_dotenv
import os
from db_config import MongoDBHandler

def main():
    # Get ENV variables from the '.env' file
    load_dotenv()
    
    # Validate required environment variables
    required_vars = ['API_ID', 'API_HASH', 'PHONE']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please copy '.env.example' to '.env' and fill in your credentials."
        )
    
    # Get Telegram API credentials
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    phone = os.getenv('PHONE')
    
    # Get MongoDB configuration
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    database_name = os.getenv('MONGODB_DATABASE', 'telegram_scraper')
    collection_name = os.getenv('MONGODB_COLLECTION', 'scraped_users')
    
    # Initialize MongoDB connection
    db_handler = MongoDBHandler(mongo_uri, database_name, collection_name)
    
    client = TelegramClient(phone, api_id, api_hash)

    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(phone)
        client.sign_in(phone, input('Enter the OTP: '))

    groups_list = []
    group = {}

    # Get's a List of Dictionaries with Group name with Group ID
    for d in client.get_dialogs():
        try:
            if d.is_group and not d.is_channel and d.name != '':
                group = {
                    "id": d.entity.id,
                    "title" : d.entity.title
                }
                groups_list.append(group)
        except:
            continue

    print('Choose a group to scrape members from:')
    i=0
    for g in groups_list:
        print(str(i) + '- ' + g['title'])
        i+=1

    g_index = input("Enter a Number: ")
    target_group = groups_list[int(g_index)]

    print('Fetching Members...')
    all_participants = []

    all_participants = client.get_participants(target_group["title"])

    print('Saving to MongoDB...')
    try:
        users_batch = []
        for user in all_participants:
            user_data = {
                'username': user.username if user.username else "",
                'first_name': user.first_name if user.first_name else "",
                'last_name': user.last_name if user.last_name else "",
                'phone': user.phone if user.phone else "",
                'user_id': user.id if user.id else "",
                'group': target_group["title"] if target_group["title"] else "",
                'group_id': target_group["id"] if target_group["id"] else ""
            }
            users_batch.append(user_data)
        
        # Save batch to MongoDB
        if users_batch:
            db_handler.insert_users_batch(users_batch)
            print(f'Members scraped successfully. Total users processed: {len(users_batch)}')
        else:
            print('No users found in the selected group.')
            
    except Exception as e:
        print(f'Error during scraping: {e}')
    finally:
        # Close database connection
        db_handler.close_connection()

if __name__ == "__main__":
    try:
        main()
    except EnvironmentError as e:
        print(f"Configuration Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
        
