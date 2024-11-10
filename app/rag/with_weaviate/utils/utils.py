import weaviate
import os
import sys
import json
import weaviate
from weaviate.classes.query import Filter
from dotenv import load_dotenv
from weaviate.exceptions import WeaviateBaseError
import requests
import inspect
import logging
from collections import Counter

# Configure logging for development
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)


# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import vector_stores.vector_stores as vector_store
import configs.configs as configs

pdf_file_path = configs.pdf_file_path
class_name = configs.class_name

# Function to check if a collection (class) exists
def check_collection_exists(client, collection_name: str) -> bool:
    try:
        return client.collections.exists(collection_name)
    except Exception as e:
        logging.warning(f" *** utils.py - Error checking if collection exists: {e}")
        return False

# Using context management if Weaviate client supports it
def reflect_weaviate_client(client):
    # Perform your operations with the client here


    attributes = dir(client)
    for attr in attributes:
        #print(attr)
        pass

    batch = client.batch
    attributes = dir(batch)
    for attr in attributes:
        print(attr)

    #print (help(client.collections))
    client.batch.dynamic=True

    print (client.batch)
    methods = [func for func in dir(client.batch) if callable(getattr(client.batch, func)) and not func.startswith("__")]

    print()
    print("Methods of client.batch:")
    for method in methods:
        print(method)

    # Alternatively, use inspect to get more detailed information
    print("\nDetailed method info from inspect:")
    for name, method in inspect.getmembers(client.batch, predicate=inspect.isfunction):
        print(f"Method: {name}, Callable: {method}")

def get_all_filenames(pdf_file_path):
    all_files = []
    for dirpath, dirnames, filenames in os.walk(pdf_file_path):
        for filename in filenames:
            if not filename.startswith('.'):  # Exclude files that start with a dot
                all_files.append(os.path.join(dirpath, filename))

    #logging.info(f"\n utils.py -- all files \n {json.dumps(all_files, indent=2)}")
    return all_files

def get_total_object_count (client):
    collection = client.collections.get(class_name)
    response = collection.query.fetch_objects()
    object_cnts = len(response.objects)

    """
    i=0
    for o in response.objects:
        i = i+1
        print(i)
        print(o.properties.get("source"), o.properties.get("page_number"))
    """

    file_counts = Counter()
    all_files= get_all_filenames(pdf_file_path)
    for filename in all_files:
        count = sum(1 for o in response.objects if o.properties.get("source") == filename)
        file_counts[filename] = count
        
    logging.info(f" === utils.py counts per file \n {json.dumps(file_counts, indent=2)}")

    # Define the path to save the JSON file
    output_file_path = "temp.txt"  # Update with your desired path

    with open(output_file_path, "w") as f:
        for i, o in enumerate(response.objects, start=1):
            f.write(f"Object {i} properties:\n")
            # Access only the properties dictionary of each object
            for key, value in o.properties.items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")  # Separate objects by a newline
    
    return file_counts


def delete_by_uuid (client, class_name, uuid) :

    collection = client.collections.get(class_name)
    collection.data.delete_by_id(
        uuid
    )


# Add a function to get collection stats
def get_collection_stats(client, class_name: str) -> dict:
    try:
        collection = client.collections.get(class_name)

        
        
        
        
        
        
    except Exception as e:
        logging.error(f"Error getting collection stats: {str(e)}", exc_info=True)
        return None
    
def get_client():
    try:
        return vector_store.create_client()
    except Exception as e:
        logging.warning(f" utils.py - Failed to create embedded client: {e}")
        return weaviate.connect_to_local(headers={"X-OpenAI-Api-Key": configs.OPENAI_API_KEY})
    
def main():
   
    client = get_client()
    get_total_object_count(client)
   
   

if __name__ == "__main__":
    main()