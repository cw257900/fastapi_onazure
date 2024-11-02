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


from dotenv import load_dotenv
load_dotenv()

# Set API keys and Weaviate URL from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")  # WEAVIATE_URL
WEAVIATE_STORE_NAME = configs.WEAVIATE_STORE_NAME  # WEAVIATE_STORE_NAME


## Function to create and return a Weaviate client object
def create_client():

    WEAVIATE_HOST = "localhost"
    WEAVIATE_HTTP_PORT = 8080
    WEAVIATE_GRPC_PORT = 50051
    headers = {"X-OpenAI-Api-Key": OPENAI_API_KEY}

    # Initialize connection params
    connection_params = ConnectionParams(
        http={"host": WEAVIATE_HOST, "port": WEAVIATE_HTTP_PORT, "secure": False, "additional_headers": headers},
        grpc={"host": WEAVIATE_HOST, "port": WEAVIATE_GRPC_PORT, "secure": False}
    )

    # client = weaviate.connect_to_local( headers = {"X-OpenAI-Api-Key": OPENAI_API_KEY})

    # client = weaviate.connect_to_embedded( headers = {"X-OpenAI-Api-Key": OPENAI_API_KEY})
    
    client = weaviate.WeaviateClient(
        embedded_options=EmbeddedOptions(
            additional_env_vars={
                "ENABLE_MODULES": "backup-filesystem,text2vec-openai,text2vec-cohere,text2vec-huggingface,ref2vec-centroid,generative-openai,qna-openai",
                "BACKUP_FILESYSTEM_PATH": "/tmp/backups",
                "persistence_data_path":"./weaviate_data"
            }
        ),
        additional_headers= {"X-OpenAI-Api-Key": OPENAI_API_KEY }
    )
    client.connect()


    return client

    

def close_client(client):
    if client:
        client.close()
        print("Weaviate client closed.")


if __name__ == "__main__":

    client = create_client()
    print (client)

