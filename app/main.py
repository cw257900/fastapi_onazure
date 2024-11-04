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

@app.get("/upload")
async def upload_data():
    response = await rag_weaviate.rag_upload()
    
    return response
    


@app.get("/query/{ask}")
async def retrive_json (ask:str):

    indexed_object= rag_weaviate.rag_retrieval( ask, limit =5 )
    #json_list = await run_in_threadpool(rag_weaviate.rag_retrieval, ask, limit =2)

    print ( " ****** main.py *****  ", indexed_object)
    return indexed_object 
    


@app.get("/prompt/{ask}")
async def read_llamindex (ask: str):
   
    response = await run_in_threadpool(rag_llamaindex.rag_lli, ask)

    if response is None:
        #logger.warning(f"No response generated for prompt: {ask}")
        return {"Prompt": "No response generated"}
    
    # Ensure response is serializable
    return {"Prompt": str(response)}
    

