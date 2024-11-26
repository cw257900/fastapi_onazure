import os
import sys
import nest_asyncio
nest_asyncio.apply()


# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Local imports
from with_weaviate.chunking import chunking_recursiveCharacterTextSplitter as doc_chunks 
from with_weaviate.utils import utils_llamaindex as utils
from with_weaviate.configs import configs
# Global variables
pdf_file_path = configs.pdf_file_path
PERSIST_DIR = configs.LLAMAINDEX_PERSISTENCE_PATH
os.environ["OPENAI_API_KEY"] = configs.OPENAI_API_KEY

from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from llama_index.core import SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core import StorageContext
from llama_index.core import SummaryIndex
from llama_index.core import VectorStoreIndex


def query_router (): 
    Settings.llm = OpenAI(model="gpt-3.5-turbo-1106", temperature=0.2)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")


    # load documents
    documents = SimpleDirectoryReader(pdf_file_path).load_data()


    # initialize settings (set chunk size)
    Settings.chunk_size = 1024
    nodes = Settings.node_parser.get_nodes_from_documents(documents)


    # initialize storage context (by default it's in-memory)
    storage_context = StorageContext.from_defaults()
    storage_context.docstore.add_documents(nodes)

    summary_index = SummaryIndex(nodes, storage_context=storage_context)
    vector_index = VectorStoreIndex(nodes, storage_context=storage_context)



    list_query_engine = summary_index.as_query_engine(
        response_mode="tree_summarize",
        use_async=True,
    )
    vector_query_engine = vector_index.as_query_engine()


def main ():
    query_router()

if __name__ =="__main__" :
    main()