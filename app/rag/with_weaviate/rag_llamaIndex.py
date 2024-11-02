import os, sys 
import uuid
import time
import os
import sys
import base64
from sentence_transformers import SentenceTransformer
from PIL import Image
import pytesseract
import requests
from pathlib import Path 
import llama_index
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

from llama_index.core import KeywordTableIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI

import openai



# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vector_stores import vector_stores as vector_store
from configs import configs

from dotenv import load_dotenv
load_dotenv()

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)


# Set API keys and Weaviate URL from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
REPLICATE_API_TOKEN=os.getenv("REPLICATE_API_TOKEN")

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")


WEAVIATE_URL = os.getenv("WEAVIATE_URL")  # WEAVIATE_URL
pdf_file_path = os.getenv("LOCAL_FILE_INPUT_PATH")
class_name = configs.WEAVIATE_STORE_NAME  # WEAVIATE_STORE_NAME
class_description = configs.WEAVIATE_STORE_DESCRIPTION

import os.path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

def load_files_from_dir ():
    print (pdf_file_path)
    reader = SimpleDirectoryReader(input_dir=pdf_file_path, recursive=True)
    # reader = SimpleDirectoryReader(input_files=["./data/input_pdfs/emphasis-text.pdf"])
    documents = reader.load_data()

    all_docs = []
    idx =0
    for  docs in reader.iter_data():
        # <do something with the documents per file>
        all_docs.extend(docs)
        idx += 1
        #print (docs)
        #print (docs[0].get_content())
        print (" == ", docs[0].get_doc_id())
        print (" == ", docs[0].metadata.get("file_name"))
        print (" ***** ", docs[0].get_text())
        print ()

def load_file_to_local_storage ():
   
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    response = query_engine.query("summary of the paper")
    print( " == summary ", response)

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

    # Either way we can now query the index
    query_engine = index.as_query_engine()
    response = query_engine.query("What did the author do growing up?")
    print(response)



# build index over data file 
def test ():

    documents = SimpleDirectoryReader("data_llama").load_data()
    index = VectorStoreIndex.from_documents( documents) #without llm when creating index
    query_engine = index.as_query_engine()
    #response = query_engine.query("sumerize the insurance document")
    response = query_engine.query("what magic of Prince is about; and Can you summarize constitution as well?")
    print(response)



if __name__ =="__main__" :
    test()