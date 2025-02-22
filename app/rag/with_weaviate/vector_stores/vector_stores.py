import os
import sys
import weaviate
from weaviate import WeaviateClient 
from weaviate.classes.init import Auth
from weaviate.connect import ConnectionParams
import weaviate
from weaviate.embedded import EmbeddedOptions


# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configs import configs

import logging
# Configure logging for development
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)


os.environ['OPENAI_API_KEY']=configs.OPENAI_API_KEY


## Function to create and return a Weaviate client object
def create_client():

    headers = {"X-OpenAI-Api-Key": configs.OPENAI_API_KEY}

    # Initialize connection params
    """
    connection_params = ConnectionParams(
        http={"host": WEAVIATE_HOST, "port": WEAVIATE_HTTP_PORT, "secure": False, "additional_headers": headers},
        grpc={"host": WEAVIATE_HOST, "port": WEAVIATE_GRPC_PORT, "secure": False}
    )
    """
    #client = weaviate.connect_to_local( headers = {"X-OpenAI-Api-Key": configs.OPENAI_API_KEY})
    """
    client = weaviate.use_async_with_embedded (
        version="1.26.1",
        headers={"X-OpenAI-Api-Key": OPENAI_API_KEY},
        port=8079,
        grpc_port=50051,
    )
    """
    
    client = weaviate.connect_to_embedded(
        version="1.27.3",
        persistence_data_path=configs.WEAVIATE_PERSISTENCE_PATH,
        headers= headers,
        environment_variables={
            "ENABLE_MODULES": "text2vec-openai,text2vec-cohere,text2vec-huggingface,ref2vec-centroid,generative-openai,qna-openai",
        }
    )
   
    logging.info (" === vectore_stores.py - embeded client initated {}".format(client))
    

    return client

    

def close_client(client):
    if client:
        client.close()
        print("Weaviate client closed.")

if __name__ == "__main__":

    client = create_client()
    print (client)
    if not client.collections.exists("Test"):
        collection = client.collections.create("Test")
    else:
        collection = client.collections.get("Test")
    collection.data.insert({"text": "this is a test " })
    print (collection)
    client.close()

