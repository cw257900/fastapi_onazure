import os 
import sys
import logging

import shutil
from llama_parse import LlamaParse
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from with_weaviate.configs import configs
pdf_file_path = configs.pdf_file_path
PERSIST_DIR = configs.LLAMAINDEX_PERSISTENCE_PATH
os.environ["OPENAI_API_KEY"] = configs.OPENAI_API_KEY


# Configure logging for development
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)

def refresh_index( storage_dir=PERSIST_DIR):
    """
    Force refresh the index by deleting existing storage and creating new index.
    
    Args:
        pdf_file_path (str): Path to directory containing PDF files
        storage_dir (str): Directory to store the index
        
    Returns:
        VectorStoreIndex: New document index or None if operation fails
    """
    # Remove existing storage if it exists
    if os.path.exists(storage_dir):
        try:
            shutil.rmtree(storage_dir)
            logging.info(f"Removed existing index storage at {storage_dir}")
        except Exception as e:
            logging.exception(f"Error removing existing storage: {str(e)}")
            return None
    
    # Create new index
    return True


def upload_to_index ( pdf_file_path, storage_dir) :

    index = None
    # set up parser
    parser = LlamaParse(
        result_type="markdown"  # "markdown" and "text" are available
    )

    # use SimpleDirectoryReader to parse our file
    file_extractor = {".pdf": parser}

    logging.info (f" === *index.py pdf_file_path {pdf_file_path}")

    for filename in os.listdir(pdf_file_path):
        try: 
            if filename == '.DS_Store' or not filename.lower().endswith('.pdf'):
                logging.debug(f"Skipping file: {filename}")
                continue

            file_path = os.path.join(pdf_file_path, filename)


            if not os.path.exists(PERSIST_DIR):
                # load the documents and create the index
                documents = SimpleDirectoryReader(
                        input_files=[file_path],
                        file_extractor=file_extractor
                    ).load_data()
        
                index = VectorStoreIndex.from_documents(documents)

                # store it for later
                index.storage_context.persist(persist_dir=PERSIST_DIR)
            else:
                # load the existing index
                storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
                index = load_index_from_storage(storage_context)

            logging.info(f" === *index.py upload data to \nIndex: {index} ;  \nPERSIST_DIR: {PERSIST_DIR} ; \nSource File: {file_path}")
            

        except Exception as e:
            logging.exception(e)
            continue


    return index

    

def retrieve_from_index(prompt, index ):

    
   

    # check if storage already exists

    PERSIST_DIR = "./storage"
    if not os.path.exists(PERSIST_DIR):
        # load the documents and create the index
        documents = SimpleDirectoryReader("data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        # store it for later
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        # load the existing index
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)


    query_engine = index.as_query_engine()
    response = query_engine.query("summary of constitution.pdf")

    logging.info( " == summary ", response)
   
    
# Function to build index over data file
def rag_lli(prompt="provide summary"):
    # Load documents from the specified path
    documents = SimpleDirectoryReader(pdf_file_path).load_data()
    
    # Create the index using the local embedding model , default is openAI's embedding
    index = VectorStoreIndex.from_documents(documents)
    
    # Create a query engine from the index
    query_engine = index.as_query_engine()
    
    # Query the index and print the response
    response = query_engine.query(prompt)

    return response



if __name__ =="__main__" :
    prompt ="summerize constitution.pdf"
    upload_to_index (pdf_file_path = pdf_file_path, storage_dir = PERSIST_DIR)
