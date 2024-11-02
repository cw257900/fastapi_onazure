import os
import weaviate.classes as wvc
import weaviate
import sys
from sentence_transformers import SentenceTransformer

# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vector_stores import vector_stores as vector_store
from utils import utils
from configs import configs
from dotenv import load_dotenv
load_dotenv()

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

import logging
logging.basicConfig(level=logging.ERROR)

# Set API keys and Weaviate URL from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")  # WEAVIATE_URL
class_name = configs.WEAVIATE_STORE_NAME  # WEAVIATE_STORE_NAME
class_description = configs.WEAVIATE_STORE_DESCRIPTION
text2vec_model=configs.text2vec_model  




# vectorizer_config=None
# multiple models: text_model for prompt; image_model for images, 
# all models need to have same dimension, otherwise, will error out 
def create_schema_multi_model (client, class_name, class_description=None) :

    if utils.check_collection_exists(client, class_name):
        print(f"Collection '{class_name}' already exists.")
        return

    try:
        collection = client.collections.create( #this is v4 weaviate
            name=class_name,
            description=class_description,
            vectorizer_config=None,  # Explicitly define `vectorizer` as "none"
            generative_config=wvc.config.Configure.Generative.openai(),

            properties=[
                wvc.config.Property (name="source",   data_type=wvc.config.DataType.TEXT),
                wvc.config.Property (name="image_file",  data_type=wvc.config.DataType.TEXT),
                wvc.config.Property (name="image",         data_type=wvc.config.DataType.BLOB),
                wvc.config.Property (name="image_content", data_type=wvc.config.DataType.TEXT),
            ],
            # Configure vector index with vector dimension 512 and HNSW indexing
            vector_index_config=wvc.config.Configure.VectorIndex.hnsw(
                distance_metric=wvc.config.VectorDistances.COSINE,
            ),

            # Optional: Configure inverted index
            inverted_index_config=wvc.config.Configure.inverted_index(
                index_null_state=True,
                index_property_length=True,
                index_timestamps=True,
            ),
        )
    
    except Exception as e:
        print(f"Error: {e}")
        #traceback.print_exc()

    finally:
        
        client.close()      

# embeded options: openai, huggingface, or none 
# vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai()  ,
# vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers( )   
# generative_config specify api to vector prompts
def create_collection(client, class_name, class_description=None,  dimension = 1536):
    """ 
    text-embedding-3-large, dimensions: 3072
    text-embedding-ada-002, dimensions: 1536
    text-embedding-3-small, dimensions: 1536

    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai( model=text2vec_model)  
    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers( ) 
    """
   
    if utils.check_collection_exists(client, class_name):
        print(f"Collection '{class_name}' already exists.")
        return

    try:
        collection = client.collections.create( #this is v4 weaviate
            name=class_name,
            description=class_description,
            # Set the vectorizer to "text2vec-openai" to use the OpenAI API for vector-related operations
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai()  ,
            # vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers( )   ,

            # Set the generative module to "generative-cohere" to use the Cohere API for RAG
            generative_config=wvc.config.Configure.Generative.cohere () ,        
            properties=[
                wvc.config.Property(
                    name="page_content",
                    data_type=wvc.config.DataType.TEXT,
                ),
                wvc.config.Property(
                    name="page_number",
                    data_type=wvc.config.DataType.INT,
                ),
                wvc.config.Property(
                    name="source",
                    data_type=wvc.config.DataType.TEXT,
                )
            ],
            # Configure the vector index
            vector_index_config=wvc.config.Configure.VectorIndex.hnsw(  # Or `flat` or `dynamic`
                distance_metric=wvc.config.VectorDistances.COSINE,
                quantizer=wvc.config.Configure.VectorIndex.Quantizer.bq(),
            ),
            
            # Configure the inverted index
            inverted_index_config=wvc.config.Configure.inverted_index(
                index_null_state=True,
                index_property_length=True,
                index_timestamps=True,
            ),
        )

        print (f" = 0. create_schem.py: {class_name} created ")
        print ()
        #print(collection)
        
    except Exception as e:
        print(f"Error: {e}")
        #traceback.print_exc()
    finally:
        
        client.close()




   
# Example usage
if __name__ == "__main__":

    #client = vector_store.client
    
    # Initialize the Weaviate client
    # client = vector_store.create_client()
    client = vector_store.connect_to_embeded()
    if (not client.is_connected()): 
        print (client.is_connected)
        client.connect()


    #without vector, use outside ; default vector = None 
    create_collection(client, class_name=class_name,class_description=class_description)

    #create_schema_multi_model (client, class_name) 

    vector_store.close_client(client)
