
import os
import sys

from dotenv import load_dotenv
load_dotenv()

WEAVIATE_STORE_NAME="PDF_COLLECTION"
WEAVIATE_STORE_DESCRIPTION="collections"
#WEAVIATE_STORE_NAME="PDF_COLLECTION"
#WEAVIATE_STORE_DESCRIPTION="PDF Collection with embeddings by Weaviate"
#WEAVIATE_STORE_NAME="OCR"
#WEAVIATE_STORE_DESCRIPTION="OCR with metadata, index and harsh"
text2vec_model="sentence-transformers/all-MiniLM-L6-v2"

# Set API keys and Weaviate URL from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")  # Weaviate API key
WEAVIATE_URL = os.getenv("WEAVIATE_URL")  # WEAVIATE_URL


class_name = "PDF_COLLECTION"

base_path =os.getcwd()
def find_data_folder(base_path, folder_name="data"):
    for root, dirs, files in os.walk(base_path):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
    return None

pdf_file_path = find_data_folder (base_path, "data")

print (" configs.py: ", pdf_file_path )