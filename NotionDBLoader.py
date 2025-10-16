from langchain_community.document_loaders import NotionDBLoader
from dotenv import load_dotenv
from getpass import getpass
import os


# NOTION_TOKEN = os.getenv('NOTION_API_KEY')
# DATABASE_ID = os.getenv('NOTION_DB_ID')
NOTION_TOKEN = getpass("Enter your Notion Integration Token: ")
DATABASE_ID = getpass("Enter your Notion Database ID: ")

loader = NotionDBLoader(
  integration_token=NOTION_TOKEN,
  database_id=DATABASE_ID,
  request_timeout_sec=30
)

docs = loader.load()
print(docs)