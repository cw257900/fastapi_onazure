import os
import sys
import logging
import json
from azure.storage.blob import BlobServiceClient
import tempfile
import asyncio  # Add this import


# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import utils
from vector_stores import vector_stores as vector_store
import vectordb_create as create
from configs import configs
class_name = configs.class_name
blob_path = configs.blob_path
blob_name = configs.blob_name
container_name = configs.AZURE_CONTAINER_NAME
connection_string = configs.AZURE_STORAGE_CONNECTION_STRING

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

# Configure logging for development
logging.basicConfig (
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)


#client = utils.get_client()

class PDFProcessor:
    def __init__(self):
        """
        Initialize PDF processor with Azure connection string
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    async def upsert_chunks_to_store(self, client , container_name=container_name, blob_path: str = blob_path):
        
        status_rtn = {
            "status": True,
            "message": [],
            "error": ['None']
        }
        try: 
            
            logging.info(f" === *blob.py - Processing blobs under \n blob path: {blob_path}; \n container: {container_name}")
            print()

            container_client = self.blob_service_client.get_container_client(container_name)
           
            # List blobs under the specified prefix
            blob_list = container_client.list_blobs(name_starts_with=blob_path)
              

            for blob in blob_list:
                temp_pdf_path = None  # Define it inside the loop so it resets for each blob
                try:
                    
                    logging.info(f"\n === *blob.py - Processing blob: {blob.name}")
                    
                    blob_client = container_client.get_blob_client(blob.name)
                    blob_data = blob_client.download_blob().readall() 

                    # Extract the original file name from the blob name
                    original_filename = os.path.basename(blob.name)
                
                    
                    # Create a temporary file with the same name as the original blob file
                    temp_dir = tempfile.gettempdir()  # Get the system temp directory
                    temp_pdf_path = os.path.join(temp_dir, original_filename)  # Full path with original filename

                    with open(temp_pdf_path, 'wb') as temp_pdf:
                        temp_pdf.write(blob_data)
                        logging.info(f" === *blob.py - Temporary PDF saved to: {temp_pdf_path}")

                    # Process the file
                    response = await create.upsert_single_file_to_store (
                        temp_pdf_path, 
                        client=client,
                        class_name=class_name  
                    )
                    

                    logging.info("\n === *blob.py - Processing Response:\n%s", json.dumps(response, indent=2))
                
                except Exception as e:
                    logging.error (
                        f"Error processing blob {blob.name}",
                        extra={"error_type": type(e).__name__, "error_message": str(e)},
                        exc_info=True
                    )
                    response["status"] = False
                    response["error"].append({
                        "code": "C003",
                        "message": f"Error while insert {blob.name} from azure blob",
                        "details": str(e)
                    })
                    continue  # Log the error and move to the next blob

            response["message"] = f"successfully uploaded blob data {blob_path}"   
                 
        except Exception as main_error:
            logging.error (
                "Blob listing or processing error",
                extra={"error_type": type(main_error).__name__, "error_message": str(main_error)},
                exc_info=True
            )
            response["status"] = False
            response["error"].append({
                    "code": "C004",
                    "message": f"Error while insert {blob_list} from azure blob",
                    "details": str(e)
             })

            raise

        finally:
            return status_rtn



    async def read_pdf_from_blob(self, client, container_name="sacontainer", blob_name: str = configs.blob_name):
        temp_pdf_path = None
        try: 
            logging.info(f" === *blob.py - Processing blob: {blob_name}")

            container_client = self.blob_service_client.get_container_client(container_name)
            blob_list = container_client.list_blobs(name_starts_with=blob_name)
            
            blob_client = container_client.get_blob_client(blob_name)
            blob_data = blob_client.download_blob().readall()       

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(blob_data)
                temp_pdf_path = temp_pdf.name
                logging.info(f"  === *blob.py - Temporary PDF saved to: {temp_pdf_path}")

            response = await create.upsert_single_file_to_store(
                temp_pdf_path, 
                client=client, 
                class_name=class_name
            )
            
            logging.info("\n === *blob.py - Processing Response:\n%s", json.dumps(response, indent=2))
                
        except Exception as e:
            logging.error(
                "Blob processing error",
                extra={ "error_type": type(e).__name__, "error_message": str(e)},
                exc_info=True
            )
            raise
        finally:
            
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    counts = utils.get_total_object_count(vector_store.create_client())
                    logging.info(f" === *blob.py - Finnally - Total objects: {counts}")
                    os.remove(temp_pdf_path)
                    logging.info(f" === *blob.py - Finnally - Temporary file removed: {temp_pdf_path}")
                except Exception as cleanup_error:
                    logging.warning(f" === *blob.py - Finally - Failed to remove temporary file: {cleanup_error}")


def main():

    # Initialize processor
    processor = PDFProcessor()
    client = utils.get_client()
    #asyncio.run(processor.upsert_chunks_to_store(client))
    asyncio.run(processor.read_pdf_from_blob(client))

if __name__ == "__main__":
    main()