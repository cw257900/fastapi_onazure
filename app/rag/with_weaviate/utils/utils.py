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


def get_total_object_count(client) -> int:
    """
    Get the total count of objects in the Weaviate instance.

    Args:
        client: Weaviate client instance (to get the base URL).

    Returns:
        int: The total count of objects, or 0 if an error occurs.
    """
    try:
        # Construct the URL for the objects endpoint
        
        url = f"{client._connection.url}/v1/objects/"

        logging.info (" === utils.py - url from get_total_object_count :{}".format(url))
        
        # Make the GET request to get the total object count
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for non-200 status codes
        
        # Extract the total count from the JSON response
        data = response.json()
        total_count = data.get("totalResults", 0)
        return total_count
    
    except requests.exceptions.RequestException as e:
        logging.warning(f" *** utils.py - Error while getting total object counts: {e}")
        return 0



def delete_by_uuid (client, class_name, uuid) :

    collection = client.collections.get(class_name)
    collection.data.delete_by_id(
        uuid
    )


# Add a function to get collection stats
def get_collection_stats(client, class_name: str) -> dict:
    try:
        collection = client.collections.get(class_name)
        count = collection.aggregate.over_all().count()
        
        stats = {
            "collection_name": class_name,
            "object_count": count,
            "exists": client.collections.exists(class_name),
            "url": client.url
        }
        
        logging.info("\nCollection Stats:\n%s", json.dumps(stats, indent=2))
        return stats
        
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
   
    logging.info (" === utils.py - weaviate version: {}".format(weaviate.__version__))
  
    client = get_client()
    count = get_total_object_count(client)
    
    logging.info (" === utils.py - total counts of objects: {}".format(count))
 

if __name__ == "__main__":
    main()