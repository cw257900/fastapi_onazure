from fastapi import FastAPI, Query, status
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from typing import Dict, Any, Optional
import uvicorn
import logging
import sys
import os

from datetime import datetime


from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag.with_weaviate.configs import configs
pdf_file_path = configs.pdf_file_path
PERSIST_DIR = configs.LLAMAINDEX_PERSISTENCE_PATH
os.environ["OPENAI_API_KEY"] = configs.OPENAI_API_KEY

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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/", response_model=Dict[str, str],summary="API Root", description="Returns available API endpoints information")
async def read_root() -> Dict[str, str]:
    """
    Root endpoint providing API usage information.
    """
    return {
        "info": "RAG API Service",
        "/query/{ask}": "Direct retrieval: type=weaviate or llamaindex",
        "/upload": "Upload data to the system: type=weaviate or llamaindex",
        "/cleanup": "Remove all data from the system: type=weaviate or llamaindex"
    }

@app.get("/upload",
         summary="Upload Data",
         description="Upload data to the RAG system using Weaviate or LlamaIndex")
async def upload(
    type: str = Query(..., pattern="^(weaviate|llamaindex)$", description="The system to upload data to: weaviate or llamaIndex")
) -> JSONResponse:
    """
    Upload endpoint to load data into the system.

    Args:
        type (str): The system to upload data to ("weaviate" or "llamaIndex")

    Returns:
        JSONResponse: The upload response
    """
    try:
        if type == "weaviate":
            response = await rag_weaviate.rag_upload()
        elif type == "llamaindex":
            response = rag_llamaindex.upload_to_llamaindex(pdf_file_path, persist_dir=PERSIST_DIR)
            response = {"index_summary": str(response)} #convert response to str 
        else:
            raise ValueError(f"Invalid type specified: {type}")

        logger.info(f"Upload to {type.capitalize()} completed successfully: {response}")
        return JSONResponse(
            content=APIResponse.success(response, f"Upload to {type} completed successfully"),
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Upload to {type} failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content=APIResponse.error(f"Upload failed: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        

@app.get(
    "/cleanup",
    summary="Cleanup Data",
    description="Remove all data from the system for the specified type (weaviate or llamaIndex)."
)
async def cleanup(type: str = Query(..., pattern="^(weaviate|llamaindex)$")) -> JSONResponse:
    """
    Cleanup endpoint to remove all data from the system for the specified type.
    :param type: The type of cleanup to perform ("weaviate" or "llamaIndex").
    """
    try:
        if type == "weaviate":
            response = await rag_weaviate.rag_cleanup()
        elif type == "llamaindex":
            response = await rag_llamaindex.cleanup()
        else:
            raise ValueError(f"Invalid cleanup type: {type}")

        logger.info(f"Cleanup completed for {type}: {response}")
        return JSONResponse(
            content=APIResponse.success(response, f"Cleanup for {type} completed successfully"),
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Cleanup failed for {type}: {str(e)}", exc_info=True)
        return JSONResponse(
            content=APIResponse.error(f"Cleanup failed for {type}: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.get("/query/{ask}",
         summary="Query the system",
         description="Query the system using weaviate or llamaindex")
async def query_system(
    ask: str,
    type: str = Query(..., pattern="^(weaviate|llamaindex)$", description="The system to query: weaviate or llamaIndex"),
    top_k: int = Query(1, description="Number of top results to retrieve ")
) -> JSONResponse:
    """
    Consolidated endpoint for querying the system using Weaviate or LlamaIndex.

    Args:
        ask (str): The query string
        type (str): The system to query ("weaviate" or "llamaIndex")
        top_k (int): Top results to retrieve for LlamaIndex queries
        limit (int): Number of results to retrieve for Weaviate queries

    Returns:
        JSONResponse: The query response
    """
    try:
      
        if type == "llamaindex":
            response = await run_in_threadpool(rag_llamaindex.query_llamaindex, ask, top_k)
        elif type == "weaviate":
            response = rag_weaviate.rag_retrieval(ask, limit=top_k)
        else:
            raise ValueError(f"Invalid type specified: {type}")

        if not response:
            return JSONResponse(
                content=APIResponse.error("No response generated", status.HTTP_404_NOT_FOUND),
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize the response to make it JSON-compatible
        serialized_response = serialize_response(response)
        
        logger.info(f"{type.capitalize()} query completed for: {ask}")
        return JSONResponse(
            content=APIResponse.success(serialized_response, f"{type.capitalize()} query processed successfully"),
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"{type.capitalize()} query failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content=APIResponse.error(f"Query failed: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def serialize_response(response):
    """
    Recursively converts datetime objects in the response to ISO format strings.
    """
    if isinstance(response, dict):
        return {key: serialize_response(value) for key, value in response.items()}
    elif isinstance(response, list):
        return [serialize_response(item) for item in response]
    elif isinstance(response, datetime):
        return response.isoformat()
    else:
        return response


async def main():
    """
    Main function for development testing.
    """
    # Add your test cases here
    pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
