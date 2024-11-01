import os 
import llama_index
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

pdf_file_path = os.path.join(os.getcwd(), "app/rag/data")


def load_file_saved_vector_to_local_storage ():
   
    documents = SimpleDirectoryReader(pdf_file_path).load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    response = query_engine.query("summary of the paper")
    print( " == summary ", response)

    # check if storage already exists
    PERSIST_DIR = "./storage"
    if not os.path.exists(PERSIST_DIR):
        # load the documents and create the index
        documents = SimpleDirectoryReader("data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        # store it for later
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        # load the existing index
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)

    # Either way we can now query the index
    query_engine = index.as_query_engine()
    response = query_engine.query("What did the author do growing up?")
    print(response)

# Function to build index over data file
def rag_lli(prompt="provide summary"):
    # Load documents from the specified path
    documents = SimpleDirectoryReader(pdf_file_path).load_data()
    
    # Create the index using the local embedding model , default is openAI's embedding
    index = VectorStoreIndex.from_documents(documents)
    
    # Create a query engine from the index
    query_engine = index.as_query_engine()
    
    # Query the index and print the response
    response = query_engine.query(prompt)

    return response



if __name__ =="__main__" :
    prompt = "sumerize the insurance document"
    rag_lli(prompt)