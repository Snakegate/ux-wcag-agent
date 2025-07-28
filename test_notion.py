print("Starting...")

from notion_client import Client

notion_token = "your_secret_key_here"
database_id = "your_database_id_here"

notion = Client(auth=notion_token)

try:
    db = notion.databases.retrieve(database_id=database_id)
    print("✅ Connection successful!")
    print("Database title:", db['title'][0]['text']['content'])
except Exception as e:
    print("❌ Error:", e)
