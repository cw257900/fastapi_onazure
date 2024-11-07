
import os
import sys

from dotenv import load_dotenv
load_dotenv()

WEAVIATE_STORE_NAME="PDF_COLLECTION"
class_name = "PDF_COLLECTION"
WEAVIATE_STORE_DESCRIPTION="collections"
WEAVIATE_PERSISTENCE_PATH="./weaviate_data"

# Set API keys and Weaviate URL from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")  # Weaviate API key
WEAVIATE_URL = os.getenv("WEAVIATE_URL")  # WEAVIATE_URL

WATCH_DIRECTORY = "./dev/rag/data"
print (" configs.py - variable WATCH_DIRECTORY: ", WATCH_DIRECTORY )

base_path =os.getcwd()
def find_data_folder(base_path, folder_name="data"): #find the path of "data" folder, as used to host pdf fils there 
    for root, dirs, files in os.walk(base_path):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
pdf_file_path = find_data_folder (base_path, "data") #this variable = None, means it couldn't fine "data" folder

print (" configs.py - variable pdf_file_path: ", pdf_file_path )