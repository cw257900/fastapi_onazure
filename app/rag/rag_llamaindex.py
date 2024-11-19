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


def upload_to_index ( pdf_file_path, persist_dir=PERSIST_DIR) :

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
                
                #documents = parse_pdf_with_page_numbers(file_path)
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


def query_index_check_storage(prompt, index, pdf_file_path=pdf_file_path ,persist_dir=PERSIST_DIR):
    # check if storage already exists, if not load first
    if not os.path.exists(PERSIST_DIR):
        # load the documents and create the index
        documents = SimpleDirectoryReader(pdf_file_path).load_data()
        index = VectorStoreIndex.from_documents(documents)
        # store it for later
        index.storage_context.persist(persist_dir)
    else:
        # load the existing index
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)


    query_engine = index.as_query_engine()
    response = query_engine.query(prompt)

    logging.info(f" === *index.py - {prompt} \n {response}")
   

    # Load documents from the specified path
    documents = SimpleDirectoryReader(pdf_file_path).load_data()
    
    # Create the index using the local embedding model , default is openAI's embedding
    index = VectorStoreIndex.from_documents(documents)
    
    # Create a query engine from the index
    query_engine = index.as_query_engine()
    
    # Query the index and print the response
    response = query_engine.query(prompt)

    return response

def query_index (index, query):
    
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
   
    logging.info (f" === query_index {query} \n{response} \n")
    return response

def parse_pdf_with_page_numbers(file_path):
    documents = []
    pdf = fitz.open(file_path)  # Open the PDF

    for page_num in range(pdf.page_count):
        page = pdf[page_num]
        text = page.get_text()
        metadata = {
            "page_number": page_num + 1  # Add page number to metadata
        }
        documents.append(Document(text=text, metadata=metadata))

    pdf.close()
    return documents

# configure response synthesizer with a custom handler for metadata
def get_response_with_metadata(response, query):
    # Iterate through each result and include page number
    results = []
    
    for node in response.source_nodes:
        
        page_number = node.metadata.get('page_number')  # get page number from metadata
        text = node.text
        results.append(f"(Page {page_number}): {text}")
        logging.info ( f" get_response_with_metadata text from file: \n {text} ")
        
    return node.metadata, "\n".join(results)

from pydantic import BaseModel
from typing import Optional, Dict, Any

class ResponseObject(BaseModel):
    summary: str
    metadata: Dict[str, Any] 
    article_content: Optional[str] 


def query_index_synthesizer (prompt, top_k=1, pdf_file_path=pdf_file_path ,persist_dir=PERSIST_DIR):

     # check if storage already exists, if not load first
    if not os.path.exists(PERSIST_DIR):
        # load the documents and create the index
        documents = SimpleDirectoryReader(pdf_file_path).load_data()
        index = VectorStoreIndex.from_documents(documents)
        # store it for later
        index.storage_context.persist(persist_dir)
    else:
        # load the existing index
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)


    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

    
    # configure retriever
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=top_k,
        return_metadata=True,  # ensures metadata (like page numbers) is included
    )

    # configure response synthesizer
    response_synthesizer = get_response_synthesizer(
        #response_mode=ResponseMode.COMPACT
        #response_mode=ResponseMode.REFINE
        response_mode=ResponseMode.SIMPLE_SUMMARIZE
        #response_mode=ResponseMode.COMPACT_ACCUMULATE
    )

    # assemble query engine
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.5)],
    )

    # query
    response = query_engine.query(prompt)
    # logging.info( f" \n=== *llamaindex.py {query} with top {similarity_top_k} :\n{response} ")
    summary = response.response.replace("Response 1: ", "")  #take out Response 1: from response object

    metadata, content_text = get_response_with_metadata(response, prompt)

    article_content =dynamic_format_text(content_text) 
   

    json_objects = []

    json_objects.append({
            "summary": summary,
            "metadata":metadata,
            "article_content": article_content
        })
    
    rtn_list = []
    for entry in json_objects: 
        list_item = { 
            "Prompt": prompt, 
            "top-k": top_k,
            "summary": entry["summary"],
            "file_name": entry["metadata"]["file_name"],
            "file_path": entry["metadata"]["file_path"],
            "file_type": entry["metadata"]["file_type"],
            "file_size": entry["metadata"]["file_size"],
            "creation_date": entry["metadata"]["creation_date"],
            "last_modified_date": entry["metadata"]["last_modified_date"],
            "article_content": entry["article_content"]
        }
        rtn_list.append (list_item)
    
    logging.info(f"top-k {top_k}")
    print(json.dumps(json_objects, indent=4))

    return rtn_list
   



def dynamic_format_text(text):
    # Replace escaped newlines and normalize spacing
    text = text.replace("\\n", "\n").replace("  ", " ")
    
    # Split text into lines and initialize formatted output
    lines = text.splitlines()
    formatted_text = ""
    
    for line in lines:
        # Strip any excess spaces from the line
        stripped_line = line.strip()

        """

        # Detect all-uppercase headers or lines with specific keywords like "Amendment", "Article"
        if stripped_line.isupper() or re.match(r"^(Amendment|Article)\s+[IVXLCDM]+", stripped_line):
            # Header line formatting with underlines
            formatted_text += f"\n\n{stripped_line}\n{'-' * len(stripped_line)}\n"
        
        """

        # Detect paragraphs (non-empty lines that aren’t headers)
        if stripped_line:
            # If the last character of formatted text is not a space or newline, add space for continuity
            if formatted_text and formatted_text[-1] not in "\n ":
                formatted_text += " "
            formatted_text += stripped_line
        
        # Add blank line for paragraph breaks when there’s an empty line
        else:
            formatted_text += "\n"

    # Replace multiple newlines with two (for section separation)
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text).strip()
    
    return formatted_text



if __name__ =="__main__" :
    upload_to_index( pdf_file_path, persist_dir=PERSIST_DIR)
   
    #query = "summarize constitution.pdf"
    #query = "What is Article IV?"
    query = "What are the key principles outlined in Constitution.pdf?"
    #query = "What's article 4 from contitution.pdf"
  
    #storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    #index = load_index_from_storage(storage_context)
    #response = query_index (index, query)
    #response = query_index_synthesizer(query)
    response = refresh_index()
 
