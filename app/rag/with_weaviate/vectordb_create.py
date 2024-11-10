import os
import json
import datetime
from datetime import datetime, timezone
# Get the current datetime in UTC and format it as RFC3339
upload_date = datetime.now(timezone.utc).isoformat()

import asyncio
import sys
import traceback 

from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import weaviate
from weaviate.classes.init import Auth
from weaviate.exceptions import WeaviateBaseError 
from weaviate.util import generate_uuid5
from langchain_huggingface import HuggingFaceEmbeddings
import  vectordb_create_schema as create_schema
import logging 

# Configure logging for development
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)


# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
# those imports used in testing from main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from chunking import chunking_recursiveCharacterTextSplitter
from embeddings import  embedding_openai 
from vector_stores import vector_stores    as vector_store
import vectordb_create_schema as vectordb_create_schema
from configs import configs
from utils import utils

pdf_file_path = configs.pdf_file_path
class_name = configs.class_name
class_description = configs.WEAVIATE_STORE_DESCRIPTION
OPENAI_API_KEY = configs.OPENAI_API_KEY



# Assuming embeddings.embeddings.aembed_documents is async and we are running this in an async environment
async def upsert_embeddings_to_vector_store(pdf_file_path, vector_store,  class_name):
    try:
        print(f"1. Inserting chunks of {pdf_file_path} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        docs = chunking_recursiveCharacterTextSplitter.get_chunked_doc(pdf_file_path)
        client = vector_store.create_client()
        collection = client.collections.get(class_name)
        embedding_huggingface =  HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Iterate through the processed docs and insert them into Weaviate
        for idx, doc in enumerate(docs):
            # Generate embeddings for the document page content, openai , next 1 line
            embedding = await embedding_openai.embeddings.aembed_documents([doc.page_content])

            """
            # huggingface embedding, next 5 lines
            # Ensure page_content is a single string, not a list
            if isinstance(doc.page_content, list):
                page_content = " ".join(doc.page_content)  # Join list items into a single string
            else:
                page_content = doc.page_content  # Already a string
            embedding = embedding_huggingface.embed_query(page_content)  # Get the first embedding in the list
            """
            
            # Get the page number from metadata or use idx + 1 if not available
            page_number = doc.metadata.get('page', idx + 1)
            
            # Create the data object with metadata
            data_object = {
                "page_content": doc.page_content,  # Add doc content as metadata
                "page_number": page_number,        # Add page number as metadata
                "source": pdf_file_path            # Optional: add file path as metadata
            }
         
            collection.data.insert(
                properties=data_object,
                uuid=generate_uuid5(json.dumps(data_object) + class_name),
                vector=embedding[0]  # Use the embedding as the vector openai only
                #vector=embedding #hugging face only 
            )

            print(f"Inserted: Page {page_number} - Chunk {idx} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            #print(embedding[0])


    
        print(f"Embeddings uploaded - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Exception occurred: {e}", exc_info=True)  # Logs with stack trace
        
        """
        Sample Error:
            1. Error: Object was not added! Unexpected status code: 422, with response body: {'error': [{'message': "id '89695fbf-06c7-599c-8da2-2c11028dd130' already exists"}]}.   
        
        """
        #traceback.print_exc()
        pass #needs to process next file if one already loaded

    finally:
       vector_store.close_client(client)



# Use context manager for client
from contextlib import asynccontextmanager
@asynccontextmanager
async def get_weaviate_client():
    client = vector_store.create_client()
    try:
        yield client
    finally:
        vector_store.close_client(client)

async def upsert_single_file_to_store(
    pdf_path: str,
    client: weaviate.Client,
    class_name: str) -> dict:
    
    response = {
        "status": True,
        "error": ['None']
    }

    try:
        if not client.collections.exists(class_name):
            create_schema.create_collection(client, class_name)
        
        collection_name = client.collections.get(class_name)
        
        # Process single PDF file
        if pdf_path.lower().endswith('.pdf'):
            logging.info(f"Processing PDF file: {pdf_path}")
            docs = chunking_recursiveCharacterTextSplitter.get_chunked_doc(pdf_path)
            
            for idx, doc in enumerate(docs):
                page_number = doc.metadata.get('page', idx + 1)
                
                data_object = {
                    "page_content": doc.page_content,
                    "page_number": page_number,
                    "source": pdf_path,
                    "uploadDate": datetime.now(timezone.utc).isoformat()
                }

                try:
                    collection_name.data.insert(
                        properties=data_object,
                        uuid=generate_uuid5(data_object),
                    )
                    logging.info(f"Inserted chunk {idx} from page {page_number}")
                except Exception as insert_error:
                    logging.error(f"Error inserting chunk: {str(insert_error)}")
                    response["status"] = False
                    response["error"].append({
                        "code": "C002",
                        "message": "Failed to insert chunk",
                        "details": str(insert_error)
                    })

    except Exception as e:
        logging.error(
            "Error processing document",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        response["status"] = False
        response["error"].append({
            "code": "C001",
            "message": "Document processing failed",
            "details": str(e)
        })
    
    finally:
        url = f"{client._connection.url}/v1/objects/"
        object_count = utils.get_total_object_count(client)
        logging.info(f" === url: from upsert_single_file_to_store.py {url}")
        logging.info(f" === object_count: {object_count}")
        pass
        #vector_store.close_client(client)
    
    return response


# weaviate v4 code
# Uploading chunks to Weaviate, by default ebedding
# if same file updated already, it will throw exception : Unexpected status code: 422, 
# with response body: {'error': [{'message': "id '8a5c4432-9a82-5f98-b9dd-5ca80b77cd13' already exists"}]}
async def upsert_chunks_to_store(
    pdf_file_path: str,
    client: weaviate.Client,
    class_name: str) -> dict:
    
    response = {
        "status": True,  # Initial status is set to True
        #"error": ['None']      # Initialize error as an empty list
        "error": []
    }
 
    if not client.collections.exists(class_name):
        create_schema.create_collection(client, class_name)
       
    try: 
        client.connect()
        collection_name = client.collections.get(class_name)
    except:
        client.connect()
        logging.info (" ==== *create.py reconnect client if needed === ")

    

     # Iterate through all files in the specified directory
    for filename in os.listdir(pdf_file_path):
        try: 
            file_path = os.path.join(pdf_file_path, filename)

            # Check if the current file is a PDF
            if os.path.isfile(file_path) and file_path.lower().endswith('.pdf') and  not filename.startswith('.') :
                
                #logging.info(f"Starting chunk insertion for: {file_path}")

                # This is a sentence-based chunker
                docs =  chunking_recursiveCharacterTextSplitter.get_chunked_doc(file_path)

                # Iterate through the processed docs and insert them into Weaviate
                for idx, doc in enumerate(docs):
                    # Get the page number from metadata or use idx + 1 if not available
                    page_number = doc.metadata.get('page', idx + 1)

                    # Create the data object with metadata
                    data_object = {
                        "page_content": doc.page_content,  # Add doc content as metadata
                        "page_number": page_number,        # Add page number as metadata
                        "source": file_path,               # Add file path as metadata
                        #"uploadDate": upload_date  # e.g., '2023-11-05T15:30:00'
                    }

                    # Insert the object along with its vector into Weaviate
                    collection_name.data.insert(
                        properties=data_object,
                        uuid=generate_uuid5(data_object),
                    )

                    print(f"Inserted: Page {page_number} - Chunk {idx} ")

                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - All chunks inserted for {file_path}")
            else: 
                if not filename.startswith('.') : #ignore .DS_Store file
                    response["error"].append({
                        "code": "C001",
                        "message": f"Warning: Skipping non-PDF file: {file_path}",
                        "details": f"Warning: Skipping non-PDF file: {file_path}"
                    })

        except Exception as e:
            
            logging.warning(f"{filename} Exception occurred: {e}")  # Logs with stack trace
            #traceback.print_exc() 

            response["status"] = False
            response["error"].append({
                "code": "C002",
                "message": f"An internal error occurred while processing the file: {filename}",
                "details": str(e)
            })

        finally:
            logging.info(f"\nDocument {file_path} Processing Status:\n%s", 
                    json.dumps(response, indent=2, ensure_ascii=False))
          
 
    # The Python client uses standard HTTP requests, which are automatically closed after the response is received.
    vector_store.close_client(client)
    
    return response 
 



async def main ():   
    pdf_file_path=configs.pdf_file_path
    async with get_weaviate_client() as client:
        status = await upsert_chunks_to_store(pdf_file_path, client, class_name)
        logging.info("\nDocument Processing Status: for {pdf_file_path}\n%s", 
                    json.dumps(status, indent=2, ensure_ascii=False))
# Entry point
if __name__ == "__main__":
    
    asyncio.run(main())