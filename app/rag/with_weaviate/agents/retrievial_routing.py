
import logging
import os
import sys
import traceback
import json
import asyncio
from typing import Any, Dict, List, Optional

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
from llama_index.core.query_engine import (
    RetrieverQueryEngine, 
    QueryEngineTool, 
    list_query_engine,
    vector_query_engine,
)

from llama_index import RouterQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.response_synthesizers import ResponseMode
from llama_index import GPTVectorStoreIndex


# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)



# Append the project's root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Local imports
from utils import utils_llamaindex as utils
from configs import configs
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
    prompt: str, top_k: int =5,  persist_dir: str = PERSIST_DIR ) -> List[Dict[str, Any]]:
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
            index=await upload_to_llamaindex()           
        else:
            storage_context=StorageContext.from_defaults(persist_dir=PERSIST_DIR)
            index=load_index_from_storage(storage_context)

        #retriver   
        retriever=index.as_retriever()
        nodes=retriever.retrieve (prompt )
        logging.info (f"\n {nodes} \n")

        #query
        #query_engine=index.as_query_engine()
       
        list_engine=QueryEngineTool.from_defaults (
            query_engine=list_query_engine,
            description=("list query"),
        )

        vector_engine=QueryEngineTool.from_defaults (
            query_engine=vector_query_engine,
            description=("vector query"),
        )

        query_engine = RouterQueryEngine(
            tools=[list_engine, vector_engine],
            router_mode="auto",
        )

        response=query_engine.query(prompt)
        logging.info (f"\n {response} \n")

    except Exception as e: 
        logging.exception(f" === *index.py Error {str(e)}")
        print(traceback.format_exc())
        raise
    

if __name__ == "__main__":
   
    # Define your query and add filters during query execution
    prompt = "what is the document about?"
  
    asyncio.run (query_llamaindex (prompt))
