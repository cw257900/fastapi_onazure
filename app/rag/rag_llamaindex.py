import os
import sys
import logging
import json
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# LlamaIndex imports
from llama_parse import LlamaParse
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    get_response_synthesizer,
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.response_synthesizers import ResponseMode

# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Local imports
from with_weaviate.utils import utils_llamaindex as utils
from with_weaviate.configs import configs

# Global variables
pdf_file_path = configs.pdf_file_path
PERSIST_DIR = configs.LLAMAINDEX_PERSISTENCE_PATH
os.environ["OPENAI_API_KEY"] = configs.OPENAI_API_KEY

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)


async def cleanup(storage_dir: str = PERSIST_DIR) -> bool:
    """
    Cleans up the storage directory to refresh the index.

    Args:
        storage_dir (str): Directory to store the index.

    Returns:
        bool: True if cleanup is successful, False otherwise.
    """
    if os.path.exists(storage_dir):
        try:
            shutil.rmtree(storage_dir)
            logging.info(f"Removed existing index storage at {storage_dir}")
        except Exception as e:
            logging.exception(f"Error removing storage: {str(e)}")
            return False
    return True


def upload_to_llamaindex(pdf_file_path: str, persist_dir: str = PERSIST_DIR) -> Optional[VectorStoreIndex]:
    """
    Uploads data from PDF files to create or update the index.

    Args:
        pdf_file_path (str): Path to the directory containing PDF files.
        persist_dir (str): Directory to store the index.

    Returns:
        Optional[VectorStoreIndex]: The created or updated index.
    """
    parser = LlamaParse(result_type="markdown")
    file_extractor = {".pdf": parser}
    index = None

    for filename in os.listdir(pdf_file_path):
        if filename == '.DS_Store' or not filename.lower().endswith('.pdf'):
            logging.debug(f"Skipping file: {filename}")
            continue

        file_path = os.path.join(pdf_file_path, filename)
        try:
            if not os.path.exists(persist_dir):
                documents = SimpleDirectoryReader(
                    input_files=[file_path],
                    file_extractor=file_extractor
                ).load_data()
                index = VectorStoreIndex.from_documents(documents)
                index.storage_context.persist(persist_dir)
            else:
                storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
                index = load_index_from_storage(storage_context)

            logging.info(f"Uploaded data to Index: {index} | File: {file_path}")
        except Exception as e:
            logging.exception(f"Error processing file {filename}: {str(e)}")
            continue

    return index


def query_llamaindex(
    prompt: str, top_k: int, pdf_file_path: str = pdf_file_path, persist_dir: str = PERSIST_DIR
) -> List[Dict[str, Any]]:
    """
    Queries the index using the synthesizer with metadata.

    Args:
        prompt (str): The query string.
        top_k (int): Number of top results to retrieve.
        pdf_file_path (str): Path to the directory containing PDF files.
        persist_dir (str): Directory to store the index.

    Returns:
        List[Dict[str, Any]]: List of formatted query results.
    """
    if not os.path.exists(persist_dir):
        documents = SimpleDirectoryReader(pdf_file_path).load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir)
    else:
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(storage_context)

    retriever = VectorIndexRetriever(index=index, similarity_top_k=top_k, return_metadata=True)
    response_synthesizer = get_response_synthesizer(response_mode=ResponseMode.SIMPLE_SUMMARIZE)

    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.5)],
    )
    response = query_engine.query(prompt)
    summary = response.response.replace("Response 1: ", "")

    results = [
        {
            "Prompt": prompt,
            "top-k": top_k,
            "summary": summary,
            "metadata": node.metadata,
            "content": utils.dynamic_format_text(node.text),
        }
        for node in response.source_nodes
    ]

    logging.info(f"Query Results: {json.dumps(results, indent=4)}")
    return results


if __name__ == "__main__":
    query = "What are the key principles outlined in Constitution.pdf?"
    response = query_llamaindex(query, top_k=2)
    print(json.dumps(response, indent=4))
