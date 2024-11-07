import os
import sys
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import ContainerClient
from azure.storage.blob.aio import BlobClient
import weaviate
from weaviate.embedded import EmbeddedOptions
import asyncio
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vector_stores import vector_stores as vector_store
from utils import utils
from configs import configs
from dotenv import load_dotenv
load_dotenv()
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

source = "MS Blob Storage"

def process_raw_files(source = source ):
    from azure.storage.blob import BlobServiceClient
    
    try:
        # Create the BlobServiceClient object
        blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        )
        
        # Get the container client
        container_client = blob_service_client.get_container_client(
            configs.AZURE_CONTAINER_NAME
        )
        
        # Test listing blobs
        blobs = list(container_client.list_blobs())
        print(f"Successfully connected! Found {len(blobs)} blobs in container.")
        return True
        
    except Exception as e:
        print(f"Error connecting to Azure Storage: {e}")
        return False

if __name__ == "__main__":
    process_raw_files(source = source )