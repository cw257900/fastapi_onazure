import sys
import os
import json
import logging
import asyncio
import weaviate
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

s#ys.path.append(os.path.dirname(os.path.abspath(__file__)))
#import with_weaviate.vectordb_retrieve as retrive 
#import with_weaviate.vectordb_create as create 
#from with_weaviate.vector_stores import vector_stores  as vectore_store


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # You can change this to DEBUG, WARNING, etc., as needed
)


# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from with_weaviate.configs import configs
from with_weaviate.vector_stores import vector_stores as vector_store
import with_weaviate.vectordb_create as create 
import with_weaviate.vectordb_retrieve as retrive 



async def rag_upload ():
    try:
        client = vector_store.create_client()
    except:
         client = weaviate.connect_to_local(port=8079, grpc_port=50050,  headers = {"X-OpenAI-Api-Key": configs.OPENAI_API_KEY}) #if embeded is not working, use local; actually should kill hanging embeded process if there are conflicts
    
    response = await create.upsert_chunks_to_store(configs.pdf_file_path,  client , configs.class_name) 

    logging.info(f"{configs.pdf_file_path} is updated to {configs.class_name} : response details: {response}")

    return response 

# Function to build index over data file
def rag_retrieval (prompt, limit=2):

    json_list = []
    print (" === rag_retrieval that rag asking ", prompt)
    hybrid_rlt = retrive.query(prompt,  limit=limit)

    print (f" === rag_retrieval that rag answer hybrid_rlt with {limit}", hybrid_rlt)
    print (hybrid_rlt)
  
    if isinstance(hybrid_rlt, dict):
        if 'error' in hybrid_rlt:
            json_list = hybrid_rlt

    else:
        idx =0
        for o in hybrid_rlt.objects:

            json_object =[]
            print(f" === {idx} rag index ")
            print(f" === {idx} rag page_content ", o.properties.get("page_content"))
            print(f" === {idx} rag score ", o.metadata.score)
            print(f" === {idx} rag explain_score ", o.metadata.explain_score)
            
            json_object = {
                "page_content": o.properties.get("page_content"),
                "page_number": o.properties.get("page_number"),
                "source": o.properties.get("source"),
                "score": o.metadata.score,
                "explain_score": str(o.metadata.explain_score).replace("\n", "")
            }
        
            indexed_object = {"index": idx, "data": json_object}

            idx =idx+1
           
            
    print ( indexed_object)
    print()
    return indexed_object
    
if __name__ =="__main__" :
    prompt = "sumerize the insurance document"
    rag_retrieval("Sumarize Constitution", limit=2)
    #rag_upload()