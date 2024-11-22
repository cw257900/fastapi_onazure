import os
import json
import sys
import logging
import traceback
import weaviate
from weaviate.classes.query import MetadataQuery

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import graphQL
from configs import configs
from utils import utils
from vector_stores import vector_stores as vector_store  
import  vectordb_create_schema as create_schema


# Configure logging for development
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)

vector_store = vector_store
pdf_file_path = configs.pdf_file_path
class_name =configs.class_name
class_description =configs.WEAVIATE_STORE_DESCRIPTION
os.environ['OPENAI_API_KEY']=configs.OPENAI_API_KEY


def create_error_response(error_code: str, custom_details: str = None) -> dict:
    error = configs.ERROR_CODES[error_code].copy()
    if custom_details:
        error["details"] = custom_details

    logging.error(json.dumps(error, indent=4))
    return {"error": error}


def query(query_text: str, client, class_name: str = class_name, limit: int =2, alpha =0.75) -> dict:
    """
    Perform a hybrid search query on the vector database.
    
    Args:
        query_text: The search query text
        class_name: The Weaviate collection name
        limit: Maximum number of results to return
        
    Returns:
        dict: Search results or error response
    """
    logging.info(f" === *retrieve.py - alpha {alpha}")
    logging.info(f" === *retrieve.py - limit {limit}")

    try: 
        error_json = None
        
        if not client.collections.exists(class_name):
            return create_error_response("R001")
        
        collection = client.collections.get(class_name)
        
        if query is None:
            pass
        else:      
            response = collection.query.hybrid(
                query=query_text,
                alpha=alpha,
                limit=limit,
                return_metadata=MetadataQuery(score=True, explain_score=True),
            )
            

            if (utils.get_total_object_count(client) == 0):
                return create_error_response("R002")
            
            else: 
                return response
        
    except Exception as e:
            
            print (traceback.format_exc())
            logging.error(f"Exception occurred: {e}")  # Logs with stack trace

            """
            Sample Error:
            1. File already uploaded: uuid will duplicate: Error: Object was not added! Unexpected status code: 422, with response body: {'error': [{'message': "id '89695fbf-06c7-599c-8da2-2c11028dd130' already exists"}]}.
            """
            return create_error_response("R003", custom_details=str(e))

    finally: 
        #logging.info(f" === url: {client._connection.url}")
        #logging.info(f" === object_count: {utils.get_total_object_count(client)}")
        #vector_store.close_client(client)
        None



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

    hybrid_rlt =  query (ask=question, limit=3)

    for o in hybrid_rlt.objects:
       
        print(json.dumps(o.properties, indent=4))
        print(o.metadata.score)
        print(o.metadata.explain_score)
        print()

    return 

  
def main():

    client = utils.get_client()
    response = query ("sumerize constitution", client,  limit =2)
    try: 
        if "error" in response: 
            logging.error (" === *retrieve.py - main " , response)
            return 
    except Exception as e: 
        idx =0
        for o in response.objects:

            json_object =[]
            
            json_object = {
                "page_content": o.properties.get("page_content"),
                "page_number": o.properties.get("page_number"),
                "source": o.properties.get("source"),
                #"uploadDate": o.properties.get("uploadDate").isoformat(), #covert date to json comparable ISO 8601 string. 
                "score": o.metadata.score,
                "explain_score": str(o.metadata.explain_score).replace("\n", "")
            }
        
            indexed_object = {"index": idx, "data": json_object}

            idx =idx+1
            logging.info (f" === *retrieve.py main index {idx}")
            logging.info (f" === *retrieve.py main json_object {json_object}")
            logging.info (" === *retrieve.py end")

# Call the main function
if __name__ == "__main__":
    main()
