import os
import sys
import logging
import traceback
import json
import asyncio
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional



from azure.storage.blob import BlobServiceClient
from azure.storage.blob import ContainerClient
from azure.storage.blob.aio import BlobClient

# LlamaIndex imports
from llama_parse import LlamaParse
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    get_response_synthesizer,
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.response_synthesizers import ResponseMode

# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Local imports
from with_weaviate.chunking import chunking_recursiveCharacterTextSplitter as doc_chunks 
from with_weaviate.utils import utils_llamaindex as utils
from with_weaviate.configs import configs
# Global variables
pdf_file_path = configs.pdf_file_path
PERSIST_DIR = configs.LLAMAINDEX_PERSISTENCE_PATH
os.environ["OPENAI_API_KEY"] = configs.OPENAI_API_KEY
blob_path = configs.blob_path
blob_name = configs.blob_name
container_name = configs.AZURE_CONTAINER_NAME
connection_string = configs.AZURE_STORAGE_CONNECTION_STRING

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)


async def cleanup(storage_dir: str = PERSIST_DIR) -> bool:
    """
    Cleans up the storage directory to refresh the index.

    Args:
        storage_dir (str): Directory to store the index.

    Returns:
        bool: True if cleanup is successful, False otherwise.
    """
    if os.path.exists(storage_dir):
        try:
            shutil.rmtree(storage_dir)
            logging.info(f"Removed existing index storage at {storage_dir}")
        except Exception as e:
            logging.exception(f"Error removing storage: {str(e)}")
            return False
    return True

async def upload_blob_to_llamaindex (storage_dir: str = PERSIST_DIR) -> Optional[VectorStoreIndex]:
    
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
           
    # List blobs under the specified prefix
    blob_list = container_client.list_blobs(name_starts_with=blob_path)

    # Create a temporary file with the same name as the original blob file
    temp_dir = os.getcwd()
    temp_dir = os.path.join(temp_dir, configs.temp_folder_for_blob)
              
    for blob in blob_list:
        temp_pdf_path = None  # Define it inside the loop so it resets for each blob
        try:
                    
            logging.info(f"\n\n === *index.py - Processing blob: {blob.name} \n")
                    
            blob_client = container_client.get_blob_client(blob.name)
            blob_data = blob_client.download_blob().readall() 

            # Extract the original file name from the blob name
            original_filename = os.path.basename(blob.name)
                
                    
           
            
            # Create the directory, ignoring if it already exists
            os.makedirs(temp_dir, exist_ok=True)
            temp_pdf_path = os.path.join(temp_dir, original_filename)  # Full path with original filename

            with open(temp_pdf_path, 'wb') as temp_pdf:
                temp_pdf.write(blob_data)
                logging.info(f" === *index.py uploading blob - Temporary PDF saved to: {temp_pdf}")

        except Exception as e:
            logging.exception (
                " === index.py - Blob listing or processing error",
                extra={"error_type": type(e).__name__, "error_message": str(e)},
                exc_info=True
            )

    logging.info( f" === *index.py - blobs copied to temp dir - {temp_dir}")

    index = await upload_to_llamaindex(temp_dir)

    # Check if the directory exists before removing it
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        logging.info(f" === *index.py - Directory '{temp_dir}' has been removed.")
    else:
        logging.info(f" === *index.py - Directory '{temp_dir}' does not exist.")

    return index



async def upload_to_llamaindex(pdf_file_path = pdf_file_path) -> Optional[VectorStoreIndex]:
    """
    Uploads data from PDF files to create or update the index.

    Args:
        pdf_file_path (str): Path to the directory containing PDF files.

    Returns:
        Optional[VectorStoreIndex]: The created or updated index.
    """
    parser = LlamaParse(result_type="markdown")
    file_extractor = {".pdf": parser}
    index = None

    logging.info ( f" === *index.py - uploading this folder: {pdf_file_path}")

    for filename in os.listdir(pdf_file_path):

        if filename == '.DS_Store' or not filename.lower().endswith('.pdf'):
            logging.debug(f" === *index.py - Skipping file: {filename}")
            continue

        file_path = os.path.join(pdf_file_path, filename)

        try:

            if not os.path.exists(PERSIST_DIR):
            

                documents = await SimpleDirectoryReader(
                    input_files=[file_path],
                    file_extractor=file_extractor
                ).aload_data()

                # Add page labels to each Document, this mess up query result
                """ 
                # this block create similar results as weaviate; the result for summary always ties to page, didn't really provide high level summary
                labeled_documents = []
                for idx, doc in enumerate(documents):
                    doc.metadata["page_label"] = f"Page {idx + 1}"  # Add custom page label
                    doc.metadata["file_name"] = filename  # Add file name for reference
                    doc.metadata["file_path"] = file_path  # Add file path for reference
                    labeled_documents.append(doc)
                """
                
                index = VectorStoreIndex.from_documents(documents)
                index.storage_context.persist(PERSIST_DIR)

            else:
                storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
                index = load_index_from_storage(storage_context)
                

            logging.info(f" === *index.py - Uploaded data to \nIndex: {index} | \nFile: {file_path} \n")

        except Exception as e:
            logging.exception(f"Error processing file {filename}: {str(e)}")
            print(traceback.format_exc())
            raise

    return index


async def query_llamaindex(
    prompt: str, top_k: int,  persist_dir: str = PERSIST_DIR ) -> List[Dict[str, Any]]:
    """
    Queries the index using the synthesizer with metadata.

    Args:
        prompt (str): The query string.
        top_k (int): Number of top results to retrieve.
        pdf_file_path (str): Path to the directory containing PDF files.
        persist_dir (str): Directory to store the index.

    Returns:
        List[Dict[str, Any]]: List of formatted query results.
    """

    try : 
        if not os.path.exists(PERSIST_DIR):
            #index = await upload_to_llamaindex()
            index = await upload_blob_to_llamaindex()
        else:
            storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
            index = load_index_from_storage(storage_context)
        
        retriever = VectorIndexRetriever(index=index, similarity_top_k=top_k, return_metadata=True)
        response_synthesizer = get_response_synthesizer(response_mode=ResponseMode.SIMPLE_SUMMARIZE)

       # query_engine = index.as_query_engine()
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            #response_synthesizer=response_synthesizer,  #synthesizer results looks weird
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.5)],
        )
       
        response = query_engine.query(prompt)
        summary = response.response.replace("Response 1: ", "")

        results =[]
        results = [
            {
                "Prompt": prompt,
                "top-k": top_k,
                "summary": summary,
                "metadata": node.metadata,
                "content": utils.dynamic_format_text(node.text),
            }
            for node in response.source_nodes
        ]

        logging.info(f"Query Results: {json.dumps(results, indent=4)}")
       
        return results

    except Exception as e: 
        logging.exception(f" === *index.py Error {str(e)}")
        print(traceback.format_exc())
        raise
    

if __name__ == "__main__":
   
    # Define your query and add filters during query execution
    query = "anything about connie?"
    specific_file_name = "what_is_constifitution.pdf"
    upload_blob_to_llamaindex ()
