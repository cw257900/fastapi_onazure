import sys
import os
import json
import logging
import asyncio
import weaviate
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#import with_weaviate.vectordb_retrieve as retrive 
#import with_weaviate.vectordb_create as create 
#from with_weaviate.vector_stores import vector_stores  as vectore_store

# Configure logging for development
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)



# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from with_weaviate.configs import configs
from with_weaviate.vector_stores import vector_stores as vector_store
import with_weaviate.vectordb_create as create 
import with_weaviate.vectordb_retrieve as retrive 
from with_weaviate.utils import utils, vectordb_cleanup as cleanup

class_name = configs.class_name

async def rag_clean_data ():
    response = {
        "status": True,  # Initial status is set to True
        #"error": ['None']      # Initialize error as an empty list
        "error": []
    }
    try: 
        client = utils.get_client()
        cleanup.delete_objects(client, class_name)

    except Exception as e:
            
            logging.warning(f" === rag_weaviate.py - rag_cleanup - Exception occurred: \n    {e}")  # Logs with stack trace
            #traceback.print_exc() 

            response["status"] = False
            response["error"].append({
                "code": "D001",
                "message": f"An internal error occurred while cleanup {class_name}",
                "details": str(e)
            })
    finally: 
        return response

async def rag_upload ():
    client = utils.get_client()
        
    response = await create.upsert_chunks_to_store(configs.pdf_file_path,  client , configs.class_name) 

    logging.info(f"{configs.pdf_file_path} is updated to {configs.class_name} : response details: {response}")

    return response 

# Function to build index over data file
def rag_retrieval (prompt, limit=3, alpha=0.75 ):

    json_list = []
    logging.info (" === rag_weaviate.py retrieval that rag asking {}".format(prompt))
    response = retrive.query(prompt,  limit=limit)

    print ()
   
  
    if isinstance(response, dict):
        if 'error' in response:
            json_list = response
            return response

    else:

        # Initialize an empty list to hold all objects' properties
        json_objects = []

        for i, o in enumerate(response.objects, start=1):
            # Extract properties into a dictionary dynamically
            object_data = {key: value for key, value in o.properties.items()}
            
            # Optionally add an index or other metadata
            json_objects.append({
                "index": i,
                "data": object_data
            })

        
        # Convert list of objects to JSON
        # json_output = json.dumps(json_objects, indent=4)
        # take out page 0
        idx=0
        for i in range(len(json_objects)):
            if json_objects[i]['data'].get("page_number") == 0: 
                idx =json_objects[i]['index']
                logging.info (f" === rag_weaviate.py - retrival_json - index {idx} page_number is 0")
                break
                
        retrieve_json = [item for item in json_objects if item["index"] != idx]

        return json.dumps(retrieve_json, indent=4)


    
    
if __name__ =="__main__" :
    prompt = "sumerize the insurance document"
    rag_retrieval("What is a Constitution? Principles and Concepts", limit=3, alpha=0.75)
    #rag_upload()