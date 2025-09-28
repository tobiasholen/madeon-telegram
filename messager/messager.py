import random
from user_scraper.db_config import MongoDBHandler
from telethon import TelegramClient, sync

class TelegramMessager:
    def __init__(self, api_id, api_hash, phone, mongo_uri, database_name, collection_name, contacted_by=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.contacted_by = contacted_by or phone  # Default to phone number if not specified
        self.db_handler = MongoDBHandler(mongo_uri, database_name, collection_name)
        self.client = TelegramClient(phone, api_id, api_hash)

        self.messages = [
            " Hello! I hope you're doing well. I wanted to reach out and connect with you here on Telegram. Looking forward to chatting with you!",
            " Hi there! I came across your profile and thought it would be great to connect. Let's stay in touch!",
            " Hey! Just wanted to say hello and see how things are going. Feel free to reach out anytime!",
            " Greetings! I hope this message finds you well. Let's connect and share some interesting conversations.",
            " Hi! I wanted to take a moment to introduce myself and say hello. Looking forward to getting to know you better!",
            " Hello! I noticed we share some common interests. Let's connect and chat about them sometime!",
            " Hey there! Just wanted to drop a quick message to say hi. Hope you're having a great day!",
            " Hi! I wanted to reach out and connect with like-minded individuals. Let's connect and share ideas!",
        ]
    
    def start(self):
        self.client.connect()
        if not self.client.is_user_authorized():
            self.client.send_code_request(self.phone)
            self.client.sign_in(self.phone, input('Enter the OTP: '))

    def stop(self):
        self.client.disconnect()
        print("Client disconnected")
        self.db_handler.close_connection()
        print("Database disconnected")

    def send_opener_message_to_non_contacted_users(self, group_id=None):
        """Send opener messages only to users who haven't been contacted"""
        non_contacted_users = self.db_handler.get_non_contacted_users(group_id)
        
        if not non_contacted_users:
            print("No non-contacted users found.")
            return 0, 0
            
        print(f"Found {len(non_contacted_users)} non-contacted users")
        
        contacted_count = 0
        failed_count = 0
        
        for user in non_contacted_users:
            result = self._send_opener_message_to_user(user)
            if result:
                contacted_count += 1
            else:
                failed_count += 1
                
        print(f"\nSummary: {contacted_count} users contacted, {failed_count} failed")
        return contacted_count, failed_count


    def _send_opener_message_to_user(self, user):
        print(f'Sending message to user: {user.get("username", "N/A")}...')
        try:
            message = random.choice(self.messages)

            self.client.send_message(user['user_id'], message)
            print(f"Message sent to {user.get('username', 'N/A')}")
            
            # Update database to mark user as contacted
            success = self.db_handler.update_user_contacted(
                user_id=user['user_id'],
                group_id=user.get('group_id'),
                message_sent=message,
                contacted_by=self.contacted_by
            )
            
            if success:
                print(f"Database updated for user: {user.get('username', 'N/A')}")
                return True
            else:
                print(f"Warning: Failed to update database for user: {user.get('username', 'N/A')}")
                return False
                
        except Exception as e:
            print(f"Failed to send message to {user.get('username', 'N/A')}: {e}")
            return False


