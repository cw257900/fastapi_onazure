
import os
import weaviate
import weaviate
import sys
import logging
# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vector_stores import vector_stores as vector_store
from configs import configs
import utils

from dotenv import load_dotenv
load_dotenv()

# Set API keys and Weaviate URL from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")  # WEAVIATE_URL
class_name = configs.class_name  # WEAVIATE_STORE_NAME

# Delete all objects in the class without deleting the schema
def delete_objects(client, class_name): 
    
    # Delete all objects in the class without deleting the schema
    utils.get_total_object_count(client)
    result = client.collections.delete(class_name) 
    logging.info ( f" === *cleanup.py  {class_name}")
    logging.info ( f" === *cleanup.py  { result}")
    return result
    
   

def main():
    client = utils.get_client()
    result = delete_objects(client, class_name)
    


if __name__ == "__main__":
    main()