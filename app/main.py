from fastapi import FastAPI
import uvicorn
from starlette.concurrency import run_in_threadpool
from datetime import datetime
import logging

from  .rag import rag_llamaindex

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  # You can change this to DEBUG, WARNING, etc., as needed
)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
def read_root():
    return {"use /prompt/'ask' to query our internal knowledge base"}

@app.get("/prompt/{ask}")
async def read_question (ask: str):
   
    response = await run_in_threadpool(rag_llamaindex.rag_lli, ask)

    # Log the prompt and response
    logger.info(f"Prompt = {ask}: Answer = {response}")
    
    if response is None:
        logger.warning(f"No response generated for prompt: {ask}")
        return {"Prompt": "No response generated"}
    
    # Ensure response is serializable
    return {"Prompt": str(response)}
    