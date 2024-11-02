from fastapi import FastAPI
import uvicorn
from starlette.concurrency import run_in_threadpool
from datetime import datetime
import logging
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .rag import rag_llamaindex
from rag import rag_weaviate

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # You can change this to DEBUG, WARNING, etc., as needed
)

#logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
def read_root():
    return {"use /prompt/'ask' to query; use /upload to load data"}

@app.get("/query/{ask}")
async def retrive_json (ask:str):

    print (" = 1. main " ,ask)
    json_list = await run_in_threadpool(rag_weaviate.rag_retrieval, ask)

    print (" = 1. main " ,json_list)
    return json_list 
    


@app.get("/prompt/{ask}")
async def read_llamindex (ask: str):
   
    response = await run_in_threadpool(rag_llamaindex.rag_lli, ask)

    # Log the prompt and response
    #logger.info(f"Prompt = {ask}: Answer = {response}")
    
    if response is None:
        #logger.warning(f"No response generated for prompt: {ask}")
        return {"Prompt": "No response generated"}
    
    # Ensure response is serializable
    return {"Prompt": str(response)}
    

