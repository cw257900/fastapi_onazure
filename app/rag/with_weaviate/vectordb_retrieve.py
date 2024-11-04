
import os
import json
import sys
import logging
import traceback
import weaviate
from weaviate import use_async_with_weaviate_cloud
from weaviate.classes.query import MetadataQuery

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import graphQL
from configs import configs
from utils import utils
from vector_stores import vector_stores as vector_store  
import  vectordb_create_schema as create_schema


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # You can change this to DEBUG, WARNING, etc., as needed
)


vector_store = vector_store
pdf_file_path = configs.pdf_file_path
class_name =configs.class_name
class_description =configs.WEAVIATE_STORE_DESCRIPTION
OPENAI_API_KEY = configs.OPENAI_API_KEY
os.environ['OPENAI_API_KEY']=OPENAI_API_KEY



def query (query,   class_name = class_name, limit = 5):
    try: 
        #client = vector_store.create_client()
        error_json = None

        try:
            client = vector_store.create_client()
            print (" xxxxxx ")
        except:
            client = weaviate.connect_to_local( headers = {"X-OpenAI-Api-Key": OPENAI_API_KEY})
            print (" yyyyyyy  ")


        print (f" ==== retrieve.py {query} " , client.collections.exists(class_name))
        print()
    
        if not client.collections.exists(class_name):
            error_json = {
                "error": {
                    "code": 1001,
                    "message": "Collection is not in system",
                    "details": "Ensure vector store created and upload data."
                }
            }
            print (" === collection doesn't exist: ", error_json)
            return error_json
        
        collection = client.collections.get(class_name)
        

        if query is None:
            pass
        else:      
            response = collection.query.hybrid(
                query=query,
                alpha=0.75,
                limit=5,
                return_metadata=MetadataQuery(score=True, explain_score=True),
            )
            print ()
            print (f" ===  retrieve.py response for limit of  {limit}====" , response)
            print(" ****** ", utils.get_total_object_count(client))
            return response
        
    except Exception as e:
            print(f"Error: {e}")  # Handles errors, such as when an object already exists to avoid duplicates
            print (traceback.format_exc())
            logging.warning(f"Exception occurred: {e}")  # Logs with stack trace

            """
            Sample Error:
            1. File already uploaded: uuid will duplicate: Error: Object was not added! Unexpected status code: 422, with response body: {'error': [{'message': "id '89695fbf-06c7-599c-8da2-2c11028dd130' already exists"}]}.
            """
            error_json = {
                "error": {
                    "code": 500,
                    "message": "An internal error occurred while processing the request.",
                    "details": str(e)
                }
            }
            return error_json

    #finally: 
        # None
        #vector_store.close_client(client)


# Sample function to use gql_getSingleObjectById
def get_query_object_by_id(client, uuid):
    # Replace {uuid} in the query with the actual UUID value
    query = graphQL.gql_getSingleObjectById.replace("{uuid}", uuid)
    result = client.query.raw(query)
    return result

# Sample function to use gql_searchObjectsByKeyword
def get_query_object_by_keyword(client, keyword):
    # Replace {uuid} in the query with the actual UUID value
    query = graphQL.gql_queryObjectsByKeyword.replace("{keyword}", keyword)
    result = client.query.raw(query)
    return result


def get_hybridsearch_object_by_keyword(client, text):
    # Replace {uuid} in the query with the actual UUID value
    query = graphQL.gql_hybridSearchByText.replace("{text}", text)
    result = client.query.raw(query)
    return result

# Function to search objects by keyword with limit
def get_hybridsearch_withLimits(client, text, limit):
    # Dynamically replace {text} and {limit} in the query
    query = graphQL.gql_hybridsearch_withLimits.replace("{text}", text).replace("{limit}", str(limit))

    result = client.query.raw(query)
    return result



def retrieve_semantic_vector_search():

    # Prompt the user to input a question for hybrid search
    question = input("Enter a question for hybrid search: ")
    """
    try:
        limit = int(input("Enter the limit for number of results to return: "))
    except ValueError:
        limit = 5  # Default limit if the input is not a valid integer
    """

    # provide summary of constitution

    hybrid_rlt =  query (ask=question, limit=1)

    print("\nResults for hybrid search:")
    for o in hybrid_rlt.objects:
       
        print(json.dumps(o.properties, indent=4))
        print(o.metadata.score)
        print(o.metadata.explain_score)
        print()

    return 

def retrieve_graphql():

    None
  
def main():
     query ("constituation",   limit = 5)

# Call the main function
if __name__ == "__main__":
    main()
