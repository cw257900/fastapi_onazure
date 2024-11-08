import os
import sys
import logging
import json
import traceback
from typing import Optional
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import ContainerClient
from azure.storage.blob.aio import BlobClient
from weaviate.embedded import EmbeddedOptions
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
import tempfile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import vectordb_create as create
import asyncio  # Add this import

# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vector_stores import vector_stores as vector_store

from configs import configs
class_name = configs.class_name

from dotenv import load_dotenv
load_dotenv()


import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

import logging

logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        force=True
    )


class PDFProcessor:
    def __init__(self, connection_string: str):
        """
        Initialize PDF processor with Azure connection string
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    async def read_pdf_from_blob(self, container_name="sacontainer", blob_name: str = configs.blob_name):
        temp_pdf_path = None
        try: 
            logging.info(f"=== Processing blob: {blob_name}")

            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            blob_data = blob_client.download_blob().readall()       

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(blob_data)
                temp_pdf_path = temp_pdf.name
                logging.info(f"Temporary PDF saved to: {temp_pdf_path}")

            response = await create.upsert_single_file_to_store(
                temp_pdf_path, 
                client=vector_store.create_client(), 
                class_name=class_name
            )
            logging.info(f" === class_name: {class_name}")
            logging.info("\nProcessing Response:\n%s", json.dumps(response, indent=2))
                
        except Exception as e:
            logging.error(
                "Blob processing error",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
        finally:
            logging.info(f"=== Processing blob is loaded: {blob_name}")
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.remove(temp_pdf_path)
                    logging.info(f"Temporary file removed: {temp_pdf_path}")
                except Exception as cleanup_error:
                    logging.warning(f"Failed to remove temporary file: {cleanup_error}")

def main():
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

    # Initialize processor
    processor = PDFProcessor(AZURE_STORAGE_CONNECTION_STRING)
    asyncio.run(processor.read_pdf_from_blob())

if __name__ == "__main__":
    main()