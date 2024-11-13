from fastapi import FastAPI
import uvicorn
from starlette.concurrency import run_in_threadpool
from datetime import datetime
import logging
import sys
import os
import json
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag import rag_llamaindex
from rag import rag_weaviate

# Configure logging for development
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed from WARNING to INFO
    handlers=[
        logging.StreamHandler()  # This ensures output to console
    ]
)


app = FastAPI()

@app.get("/")
def read_root():
    return {"use /prompt/'ask' to query; use /upload to load data; /cleanup to remove data"}

@app.get("/upload")
async def upload():
    response = await rag_weaviate.rag_upload_from_blob()
    logging.info (f" === main.py - upload {response}")
    return response
    
@app.get("/cleanup")
async def cleanup():
    
    response = await rag_weaviate.rag_cleanup()
    logging.info(f" === main.py - cleanup {response}")
    return response


@app.get("/prompt/{ask}")
async def read_llamindex (ask: str):
   
    response = await run_in_threadpool(rag_llamaindex.rag_lli, ask)

    if response is None:
        #logger.warning(f"No response generated for prompt: {ask}")
        return {"Prompt": "No response generated"}
    
    # Ensure response is serializable
    return {"Prompt": str(response)}

@app.get("/query/{ask}")
async def retrieve(ask: str):
    indexed_object =  rag_weaviate.rag_retrieval(ask, limit=2)
    logging.info (f" === main.py - retrieve {indexed_object}")

    return indexed_object

async def main():
    # Call retrieve_json with a test query
    #response = await upload ()
    #reponse = await retrieve("constitution")
    #response = await cleanup()
    response = await read_llamindex()
   

# Entry point
if __name__ == "__main__":
    asyncio.run(main())