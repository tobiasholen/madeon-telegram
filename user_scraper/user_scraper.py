from db_config import MongoDBHandler
from telethon import TelegramClient


class TelegramUserScraper:
    def __init__(self, api_id, api_hash, phone, mongo_uri, database_name, collection_name):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.db_handler = MongoDBHandler(mongo_uri, database_name, collection_name)
        self.client = TelegramClient(phone, api_id, api_hash)


    async def start(self):
        """Start the Telegram client and connect"""
        self.client = TelegramClient('session_name', self.api_id, self.api_hash)
        await self.client.start(phone=self.phone)
        print("Client started")

    async def scrape_users_from_channel(self, channel_username):
        """Scrape users from a specified Telegram channel"""
        if not self.client:
            raise Exception("Client not started. Call start() first.")

        try:
            channel = await self.client.get_entity(channel_username)
            participants = await self.client.get_participants(channel)

            for user in participants:
                user_data = {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'phone': user.phone,
                    'access_hash': user.access_hash,
                    'is_bot': user.bot,
                    'is_verified': getattr(user, 'verified', False),
                    'is_restricted': getattr(user, 'restricted', False),
                    'status': str(user.status) if user.status else None,
                }
                self.db_handler.insert_user(user_data)

            print(f"Scraped {len(participants)} users from {channel_username}")

        except Exception as e:
            print(f"Error scraping users from channel {channel_username}: {e}")

    async def stop(self):
        """Disconnect the Telegram client"""
        await self.client.disconnect()
        print("Client disconnected")
        self.db_handler.close_connection()

