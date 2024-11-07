import os
import sys
import logging
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


# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vector_stores import vector_stores as vector_store

from configs import configs
class_name = configs.class_name

from dotenv import load_dotenv
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




class PDFProcessor:
    def __init__(self, connection_string: str):
        """
        Initialize PDF processor with Azure connection string
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    def read_pdf_from_blob (self , container_name="sacontainer", blob_name: str = "dev/rag/data/constitution.pdf" ):
        try: 
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # Get blob client
            blob_client = container_client.get_blob_client(blob_name)
            
            # Download the PDF blob as binary data
            blob_data = blob_client.download_blob().readall()       

            # Save the PDF to a temporary file to be used with PyPDFLoader
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(blob_data)
                temp_pdf_path = temp_pdf.name
                print ("temp file path ", temp_pdf_path)

            create.upsert_chunks_to_store (temp_pdf_path, client = vector_store.create_client() , class_name=class_name)

            """
            # Load the PDF using PyPDFLoader
            loader = PyPDFLoader(temp_pdf_path)
            pages = loader.load()

            # Process or print the text from each page
            for page in pages:
                #print(page.page_content)
                None
            """

            # Clean up the temporary file after processing
            os.remove(temp_pdf_path)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            raise


def main():
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

    # Initialize processor
    processor = PDFProcessor(AZURE_STORAGE_CONNECTION_STRING)
    processor.read_pdf_from_blob()

if __name__ == "__main__":
    main()