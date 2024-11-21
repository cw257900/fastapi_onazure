import sys
import os
import asyncio
import traceback

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

import logging
# Configure logging for development
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from with_weaviate.configs import configs
from with_weaviate.vectordb_create_blob  import PDFProcessor
import with_weaviate.vectordb_create as create 
from with_weaviate.utils import utils, vectordb_cleanup as cleanup
import with_weaviate.vectordb_retrieve as retrive 
from with_weaviate.utils import utils

class_name = configs.class_name
client = utils.get_client()

async def rag_upload_from_blob(client=client):
    processor = PDFProcessor()
    response = await processor.upsert_chunks_to_store(client) 

    logging.info(f"{configs.base_path} is updated to {configs.class_name} : response details: {response}")

    return response 

async def rag_cleanup (client =client):
    response = {
        "status": True,  # Initial status is set to True
        #"error": ['None']      # Initialize error as an empty list
        "error": []
    }
    try: 
        response = cleanup.delete_objects(client, class_name)
        cnt = utils.get_total_object_count(client)
        logging.info (f"\n === rag_retrieve.py - cleanup {class_name} \n status: {response}; \n counts: {cnt}")

    except Exception as e:
        traceback.print_exc()

    return response
      
    
async def rag_upload (client=client):
    
    processor = PDFProcessor()
    response = await processor.upsert_chunks_to_store(client) 

    logging.info(f"{configs.pdf_file_path} is updated to {configs.class_name} : response details: {response}")

    return response 

# Function to build index over data file
def rag_retrieval (prompt,client=client, limit=3, alpha=0.75 ):

    logging.info (" === rag_weaviate.py retrieval that rag asking {}".format(prompt))
    response = retrive.query(prompt, client, limit=limit, alpha=alpha)
  
    if isinstance(response, dict):
        if 'error' in response:
        
            logging.error (f" === rag_weaviate.py {response}")
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

        logging.info (f" === rag_weaviate.py - retrieve_json: {retrieve_json}")

        return retrieve_json


    
    
if __name__ =="__main__" :
    prompt = "sumerize the insurance document"
    #rag_retrieval("What is a Constitution? Principles and Concepts", limit=3, alpha=0.75)

    asyncio.run(rag_upload(client))
    utils.get_total_object_count()
    
    #response = requests.get("http://localhost:8079/v1/schema")
    #logging.info (f" === utils.py \n {response.json()} \n") 