from user_scraper.db_config import MongoDBHandler
from telethon import TelegramClient, sync


class TelegramUserScraper:
    def __init__(self, api_id, api_hash, phone, mongo_uri, database_name, collection_name):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.db_handler = MongoDBHandler(mongo_uri, database_name, collection_name)
        self.client = TelegramClient(phone, api_id, api_hash)

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

    def _get_available_groups(self):
        groups_list = []
        group = {}

        # Get's a List of Dictionaries with Group name with Group ID
        for d in self.client.get_dialogs():
            try:
                if d.is_group and not d.is_channel and d.name != '':
                    group = {
                        "id": d.entity.id,
                        "title" : d.entity.title
                    }
                    groups_list.append(group)
            except Exception as e:
                print('Skipping a group due to an error', e)
                continue
        
        return groups_list
    
    def _save_users_to_db(self, users, target_group):
        print('Saving to MongoDB...')
        total_users_processed = 0

        users_batch = []
        for user in users:
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
            self.db_handler.insert_users_batch(users_batch)
            total_users_processed += len(users_batch)
        else:
            print('No users found in the selected group.')
        
        print(f'Total users processed: {total_users_processed}')


    def scrape_users_from_all_groups(self):
        groups_list = self._get_available_groups()

        # Extract Users from the Group and save to MongoDB
        for group_name in groups_list:
            # Iterates over List of Dictionaries to extract Users
            target_group = group_name
            all_participants = []
            all_participants = self.client.get_participants(target_group["title"])

            print('Fetching Members from {}\nSaving to MongoDB'.format(target_group["title"]))

            self._save_users_to_db(all_participants, target_group)

    def scrape_users_from_single_group(self):
        groups_list = self._get_available_groups()

        print('Choose a group to scrape members from:')
        i=0
        for g in groups_list:
            print(str(i) + '- ' + g['title'])
            i+=1

        g_index = input("Enter a Number: ")
        target_group = groups_list[int(g_index)]

        print('Fetching Members...')
        all_participants = []
        all_participants = self.client.get_participants(target_group["title"])

        self._save_users_to_db(all_participants, target_group)
