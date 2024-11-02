import os
import json
import datetime
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
import logging 

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # You can change this to DEBUG, WARNING, etc., as needed
)


# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from chunking import chunking_recursiveCharacterTextSplitter
from embeddings import  embedding_openai 
from vector_stores import vector_stores    as vector_store
import vectordb_create_schema as vectordb_create_schema
from configs import configs
from utils import utils

from dotenv import load_dotenv
load_dotenv()

# Set API keys and Weaviate URL from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")  # Weaviate API key
WEAVIATE_URL = os.getenv("WEAVIATE_URL")  # WEAVIATE_URL
#pdf_file_path =  os.getenv("LOCAL_FILE_INPUT_PATH")
pdf_file_path = os.path.join(os.getcwd(), "data")

print (" === pdf_file_path: ", pdf_file_path)
print ()

class_name =configs.WEAVIATE_STORE_NAME
class_description =configs.WEAVIATE_STORE_DESCRIPTION
os.environ["OPENAI_API_KEY"]  = OPENAI_API_KEY
    


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
        logging.warning(f"Exception occurred: {e}", exc_info=True)  # Logs with stack trace
        
        """
        Sample Error:
            1. Error: Object was not added! Unexpected status code: 422, with response body: {'error': [{'message': "id '89695fbf-06c7-599c-8da2-2c11028dd130' already exists"}]}.   
        
        """
        #traceback.print_exc()
        pass #needs to process next file if one already loaded

    finally:
       vector_store.close_client(client)


# weaviate v4 code
# Uploading chunks to Weaviate, by default ebedding
# if same file updated already, it will throw exception : Unexpected status code: 422, 
# with response body: {'error': [{'message': "id '8a5c4432-9a82-5f98-b9dd-5ca80b77cd13' already exists"}]}

def upsert_chunks_to_store(pdf_dir_path, vector_store, class_name):
    status = False

    client = vector_store.create_client()
    collection_name = client.collections.get(class_name)

     # Iterate through all files in the specified directory
    for filename in os.listdir(pdf_dir_path):
        try: 
            file_path = os.path.join(pdf_dir_path, filename)

            logging.info("uploading files under: " , file_path)

            # Check if the current file is a PDF
            if os.path.isfile(file_path) and file_path.lower().endswith('.pdf') and  not filename.startswith('.') :
                print(f"1. Inserting chunks of {file_path} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # This is a sentence-based chunker
                docs = chunking_recursiveCharacterTextSplitter.get_chunked_doc(file_path)

                # Iterate through the processed docs and insert them into Weaviate
                for idx, doc in enumerate(docs):
                    # Get the page number from metadata or use idx + 1 if not available
                    page_number = doc.metadata.get('page', idx + 1)

                    # Create the data object with metadata
                    data_object = {
                        "page_content": doc.page_content,  # Add doc content as metadata
                        "page_number": page_number,        # Add page number as metadata
                        "source": file_path               # Add file path as metadata
                    }

                    # Insert the object along with its vector into Weaviate
                    collection_name.data.insert(
                        properties=data_object,
                        uuid=generate_uuid5(data_object),
                    )

                    print(f"Inserted: Page {page_number} - Chunk {idx} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - All chunks inserted for {file_path}")
            else: 
                print(f"Skipping non-PDF file: {file_path}")
           

        except Exception as e:
            print(f"Error: {e}")  # Handles errors, such as when an object already exists to avoid duplicates
            logging.warning(f"Exception occurred: {e}")  # Logs with stack trace

            """
            Sample Error:
            1. File already uploaded: uuid will duplicate: Error: Object was not added! Unexpected status code: 422, with response body: {'error': [{'message': "id '89695fbf-06c7-599c-8da2-2c11028dd130' already exists"}]}.

            """
            pass #go to next file

 
    # The Python client uses standard HTTP requests, which are automatically closed after the response is received.
    vector_store.close_client(client)

    return status





def upsert_multi_models (pdf_file_path, vector_store, class_name):
    None

def main ():
    print(pdf_file_path)
    print(class_name)
    print()

    # Use asyncio.run to run the async function
    # asyncio.run(upsert_embeddings_to_vector_store(pdf_file_path, vector_store=vector_store, class_name=class_name))
    upsert_chunks_to_store(pdf_file_path, vector_store, class_name)
   

# Entry point
if __name__ == "__main__":
    main()




