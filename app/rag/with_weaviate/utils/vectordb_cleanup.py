
import os
import weaviate
import weaviate
import sys

# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vector_stores import vector_store as vector_store
from configs import configs

from dotenv import load_dotenv
load_dotenv()

# Set API keys and Weaviate URL from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")  # WEAVIATE_URL
WEAVIATE_STORE_NAME = configs.WEAVIATE_STORE_NAME  # WEAVIATE_STORE_NAME

   
def delete_class(client, class_name):
    client.schema.delete_class(class_name)

    # Print the class names (collections)
    print(" *** Existing collections (classes)  ***  ")
    schema = client.schema.get()
    for cls in schema['classes']:
        print(f" - {cls['class']}")

    print()

def main():

    client = vector_store.client
    collection_for_deletion = "PDF_COLLECTION"
    delete_class(client, collection_for_deletion)
    


if __name__ == "__main__":
    main()