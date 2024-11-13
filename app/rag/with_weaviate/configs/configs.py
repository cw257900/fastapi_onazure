
import os
import sys
import logging
from dotenv import load_dotenv
load_dotenv()

# Configure logging for development
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)

# LlamaIndex
LLAMAINDEX_PERSISTENCE_PATH ="./llamaindex_data"



#weaviate and azure 
class_name = "PDF_COLLECTION"
WEAVIATE_STORE_DESCRIPTION="collections"
WEAVIATE_PERSISTENCE_PATH="./weaviate_data"

# Set API keys and Weaviate URL from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")  # Weaviate API key
WEAVIATE_URL = os.getenv("WEAVIATE_URL")  # WEAVIATE_URL
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME =  "sacontainer" 
AZURE_WATCH_DIRECTORY = "rag/data"
blob_name = "rag/data/constitution.pdf"
blob_path = "rag/data"
logging.info (" === configs.py - blob_name for azure: {}".format(blob_name))

#chunk_size=5000
#chunk_overlap=300
#SUPPORTED_FILE_TYPES = ['.pdf']
#BATCH_SIZE = 100 



base_path =os.getcwd()
def find_data_folder(base_path, folder_name="data"): #find the path of "data" folder, as used to host pdf fils there 
    for root, dirs, files in os.walk(base_path):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
pdf_file_path = find_data_folder (base_path, "data") #this variable = None, means it couldn't fine "data" folder
logging.info (" === configs.py - pdf_file_path : {}".format(pdf_file_path))

ERROR_CODES = {
    "R001": { #retrieve
        "code": "R001",
        "message": "Collection is not in system",
        "details": "Ensure vector store created and have data uploaded."
    },
    "R002": {
        "code": "R002",
        "message": "Vector Collection is created, but has no data yet",
        "details": "Vector Collection is created, but has no data yet"
    },
    "R003": {
        "code": "R003",
        "message": "An internal error occurred while processing the request.",
        "details": "Generic error message - details will be populated at runtime"
    },
    "C001": { #create
        "code": "C001",
        "message": "Non-PDF file skipped",
        "details": "File type not supported"
    },
    "C002": {
        "code": "C002",
        "message": "Internal processing error",
        "details": "Error during document processing"
    },
     "C003": {
        "code": "C003",
        "message": "Internal processing error",
        "details": "Error while upload azure blob data"
    },
     "C004": {
        "code": "C004",
        "message": "Internal processing error",
        "details": "Error while upload azure list of blob path"
    },
    "D001": {
        "code": "D001",
        "message": "Internal processing error",
        "details": "Error during cleanup"
    }
}