from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from typing import Dict, Any, Optional
import uvicorn
import logging
import sys
import os
import json
import asyncio

from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag import rag_llamaindex, rag_weaviate

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG API",
    description="REST API for RAG (Retrieval Augmented Generation) operations",
    version="1.0.0"
)

class APIResponse:
    """Standard API response format"""
    @staticmethod
    def success(data: Any, message: str = "Success") -> Dict[str, Any]:
        return {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def error(message: str, status_code: int) -> Dict[str, Any]:
        return {
            "status": "error",
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/", response_model=Dict[str, str],summary="API Root", description="Returns available API endpoints information")
async def read_root() -> Dict[str, str]:
    """
    Root endpoint providing API usage information.
    """
    return {
        "info": "RAG API Service",
        "/prompt/{ask}": "Query using LlamaIndex",
        "/query/{ask}": "Direct retrieval from Weaviate",
        "/upload": "Upload data to the system",
        "/cleanup": "Remove all data from the system"
    }

@app.get("/upload",
         summary="Upload Data",
         description="Upload data to the RAG system")
async def upload() -> JSONResponse:
    """
    Upload endpoint to load data into the system.
    """
    try:
        response = await rag_weaviate.rag_upload()
        logger.info(f"Upload completed: {response}")
        return JSONResponse(
            content=APIResponse.success(response, "Upload completed successfully"),
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content=APIResponse.error(f"Upload failed: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@app.get("/cleanup",
         summary="Cleanup Data",
         description="Remove all data from the system")
async def cleanup() -> JSONResponse:
    """
    Cleanup endpoint to remove all data from the system.
    """
    try:
        response = await rag_weaviate.rag_cleanup()
        logger.info(f"Cleanup completed: {response}")
        return JSONResponse(
            content=APIResponse.success(response, "Cleanup completed successfully"),
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content=APIResponse.error(f"Cleanup failed: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@app.get("/prompt/{prompt}",
         summary="LlamaIndex Query",
         description="Query the system using LlamaIndex")
async def read_llamaindex(prompt: str, top_k=1) -> JSONResponse:
    """
    Endpoint to query the system using LlamaIndex.
    
    Args:
        ask (str): The query string
        
    Returns:
        JSONResponse: The query response
    """
    try:
        response = await run_in_threadpool(rag_llamaindex.query_index_synthesizer, prompt, top_k)

        if response is None:
            return JSONResponse(
                content=APIResponse.error("No response generated", status.HTTP_404_NOT_FOUND),
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return JSONResponse(
            content=APIResponse.success(response, "Query processed successfully"),
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"LlamaIndex query failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content=APIResponse.error(f"Query failed: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@app.get("/query/{ask}",
         summary="Weaviate Query",
         description="Direct retrieval from Weaviate")
async def retrieve(ask: str, limit: int = 2) -> JSONResponse:
    """
    Endpoint for direct retrieval from Weaviate.
    
    Args:
        ask (str): The query string
        limit (int): Maximum number of results to return
        
    Returns:
        JSONResponse: The retrieval results
    """
    try:
        indexed_object = rag_weaviate.rag_retrieval(ask, limit=limit)
        logger.info(f"Retrieval completed for query: {ask}")
        return JSONResponse(
            content=APIResponse.success(indexed_object, "Retrieval completed successfully"),
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Weaviate retrieval failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content=APIResponse.error(f"Retrieval failed: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def main():
    """
    Main function for development testing.
    """
    # Add your test cases here
    pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
