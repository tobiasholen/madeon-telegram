from dotenv import load_dotenv
import os
from telethon import TelegramClient, sync
from user_scraper.user_scraper import TelegramUserScraper

def main():
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

    scraper = TelegramUserScraper(api_id, api_hash, phone, mongo_uri, database_name, collection_name)
    try:
        scraper.start()
        scraper.scrape_users_from_all_groups()
        # scraper.scrape_users_from_single_group()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    try:
        main()
    except EnvironmentError as e:
        print(f"Configuration Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)