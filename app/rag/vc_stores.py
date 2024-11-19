import os 
import sys
import logging
import json
import shutil
import re
from typing import Any, Dict
from datetime import datetime, timezone

from llama_index.core import Document
import fitz  # PyMuPDF for PDF parsing
from llama_parse import LlamaParse
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import (
    Settings,
    get_response_synthesizer,
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.data_structs import Node
from llama_index.core.schema import NodeWithScore
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core import get_response_synthesizer

from weaviate import WeaviateClient

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from with_weaviate.utils import utils
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
  

import weaviate
from llama_index.vector_stores.weaviate import WeaviateVectorStore

# creating a Weaviate client
client = utils.get_client()

# construct vector store
vector_store = WeaviateVectorStore(weaviate_client=client)

print("Current Directory:", os.getcwd())
documents = SimpleDirectoryReader(pdf_file_path).load_data()



from llama_index.core import StorageContext
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from IPython.display import Markdown, display

# configure response synthesizer with a custom handler for metadata
def get_response_with_metadata(response):
    # Iterate through each result and include page number
    results = []
    
    for node in response.source_nodes:
        
        page_number = node.metadata.get('page_number')  # get page number from metadata
        text = node.text
        results.append(f"(Page {page_number}): {text}")
        #logging.info ( f" get_response_with_metadata text from file: \n {text} ")
        
    return node.metadata, "\n".join(results)


# If you want to load the index later, be sure to give it a name!
vector_store = WeaviateVectorStore(
    weaviate_client=client, index_name="PDF_COLLECTION"
)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context
)

print (" *****  index" , index)
query_engine = index.as_query_engine()
try : 
    response = query_engine.query("How were deputies to the Constitutional Convention chosen?")
    metadata, content_text = get_response_with_metadata(response)
except Exception as e:
    print (e)

#display(Markdown(f"<b>{response}</b>"))
print (response)
print (content_text)