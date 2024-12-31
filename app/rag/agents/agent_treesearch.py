
import logging
import os
import sys
import traceback
import json
import asyncio
import nest_asyncio
nest_asyncio.apply()

from typing import Any, Dict, List, Optional


# LlamaIndex imports
from llama_parse import LlamaParse
from llama_index.core import (
    VectorStoreIndex,
    SummaryIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    get_response_synthesizer,
    SimpleKeywordTableIndex,
    SQLDatabase,
    Settings,
)
from llama_index.core.retrievers import VectorIndexRetriever ,VectorIndexAutoRetriever
from llama_index.core.query_engine import (
    RouterQueryEngine, 
    RetrieverQueryEngine,
    NLSQLTableQueryEngine,
    FLAREInstructQueryEngine,
)
from llama_index.core.tools import QueryEngineTool,ToolMetadata
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.selectors import (
    PydanticMultiSelector,
    PydanticSingleSelector,
    LLMSingleSelector, 
    LLMMultiSelector,
)
from llama_index.core.storage import StorageContext
from llama_index.core.vector_stores import MetadataInfo, VectorStoreInfo
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.agent.lats import LATSAgentWorker


# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)


# Append the project's root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Local imports
from with_weaviate.utils import utils_llamaindex as utils
from with_weaviate.configs import configs
# Global variables
pdf_file_path = configs.pdf_file_path
PERSIST_DIR = configs.LLAMAINDEX_PERSISTENCE_PATH
os.environ["OPENAI_API_KEY"] = configs.OPENAI_API_KEY

llm = OpenAI(model="gpt-4-turbo", temperature=0.6, api_key=os.environ["OPENAI_API_KEY"])
embed_model=OpenAIEmbedding(
            model_name='text-embedding-3-small',
            embed_batch_size=10,
            timeout=120.0,
            max_retries=3,
            api_key=os.environ["OPENAI_API_KEY"]
)

Settings.llm = llm
Settings.embed_model = embed_model


blob_path = configs.blob_path
blob_name = configs.blob_name
container_name = configs.AZURE_CONTAINER_NAME
connection_string = configs.AZURE_STORAGE_CONNECTION_STRING

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)


async def query_llamaindex(
    prompt: str, top_k: int =5,  persist_dir: str = PERSIST_DIR ) -> List[Dict[str, Any]]:
    

    try : 

        # load documents
        documents = SimpleDirectoryReader(pdf_file_path).load_data()
        index = VectorStoreIndex.from_documents(
            documents,
        )

        index_query_engine = index.as_query_engine(similarity_top_k=2)

        flare_query_engine = FLAREInstructQueryEngine(
            query_engine=index_query_engine,
            max_iterations=7,
            verbose=True,
        )

        response = flare_query_engine.query(prompt)
        print ("FLAREInstructQueryEngine")
        print (response)

       
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
        vector_engine=QueryEngineTool.from_defaults (
            query_engine=vector_query_engine,
            description=("vector query"),
        )

        
        list_tool = QueryEngineTool.from_defaults(
            query_engine=list_query_engine,
            description=(
                "Useful for summarization questions."
            ),
        )

        vector_tool = QueryEngineTool.from_defaults(
            query_engine=vector_query_engine,
            description=(
                "Useful for retrieving specific context."
            ),
        )


        keyword_index = SimpleKeywordTableIndex(nodes, storage_context=storage_context)

        keyword_tool = QueryEngineTool.from_defaults(
            query_engine=vector_query_engine,
            description=(
                "Useful for retrieving specific context using keywords"
            ),
        )
        
      

        vector_store_info = VectorStoreInfo(
        content_info="articles about different cities",
        metadata_info=[
            MetadataInfo(
                name="title", type="str", description="The name of the city"
            ),
        ],
        )
        vector_auto_retriever = VectorIndexAutoRetriever(
            vector_index, vector_store_info=vector_store_info
        )

        retriever_query_engine = RetrieverQueryEngine.from_args(
            vector_auto_retriever, llm=OpenAI(model="gpt-4")
        )

        vector_tool = QueryEngineTool.from_defaults(
            query_engine=retriever_query_engine,
            description=(
                f"Useful for answering semantic questions about different cities"
            ),
        )

        query_engine = RouterQueryEngine(
            selector=PydanticSingleSelector.from_defaults(),
            query_engine_tools=[
                list_tool,
                vector_tool,
                keyword_tool
            ],
        )

        #response=query_engine.query(prompt)
        #logging.info (f"\n {response} \n")
        #print(str(response.metadata["selector_result"]))

        
    except Exception as e: 
        logging.exception(f" === *index.py Error {str(e)}")
        print(traceback.format_exc())
        raise
    
async def create_index ():

    if not os.path.exists("storage/lyft"):
        # load data
        lyft_docs = SimpleDirectoryReader(
            input_files=["data/10k/lyft_2021.pdf"]
        ).load_data()
        uber_docs = SimpleDirectoryReader(
            input_files=["data/10k/uber_2021.pdf"]
        ).load_data()

        # build index
        lyft_index = VectorStoreIndex.from_documents(lyft_docs)
        uber_index = VectorStoreIndex.from_documents(uber_docs)

        # persist index
        lyft_index.storage_context.persist(persist_dir="storage/lyft")
        uber_index.storage_context.persist(persist_dir="storage/uber")
    else:
        storage_context = StorageContext.from_defaults(
            persist_dir="storage/lyft"
        )
        lyft_index = load_index_from_storage(storage_context)

        storage_context = StorageContext.from_defaults(
            persist_dir="storage/uber"
        )
        uber_index = load_index_from_storage(storage_context)

 
    return lyft_index, uber_index


async def query_tools():

    lyft_index, uber_index = await create_index ()
    lyft_engine = lyft_index.as_query_engine(similarity_top_k=3)
    uber_engine = uber_index.as_query_engine(similarity_top_k=3)

    query_engine_tools = [
        QueryEngineTool(
            query_engine=lyft_engine,
            metadata=ToolMetadata(
                name="lyft_10k",
                description=(
                    "Provides information about Lyft financials for year 2021. "
                    "Use a detailed plain text question as input to the tool. "
                    "The input is used to power a semantic search engine."
                ),
            ),
        ),
        QueryEngineTool(
            query_engine=uber_engine,
            metadata=ToolMetadata(
                name="uber_10k",
                description=(
                    "Provides information about Uber financials for year 2021. "
                    "Use a detailed plain text question as input to the tool. "
                    "The input is used to power a semantic search engine."
                ),
            ),
        ),
    ]

    return query_engine_tools

async def query_agent():
    print(" 111 query_agent ")
    query_engine_tools = await query_tools()
    agent_worker = LATSAgentWorker.from_tools(
        query_engine_tools,
        llm=llm,
        num_expansions=2,
        max_rollouts=3,
        verbose=True,
    )
    agent = agent_worker.as_agent()

    query = (
        "Given the risk factors of Uber and Lyft described in their 10K files, "
        "which company is performing better? Please use concrete numbers to inform your decision."
    )

    # Create task
    task = agent.create_task(query)

    # run initial step
    step_output =  agent.run_step(task.task_id)  

    for step in (
        step_output.task_step.step_state["root_node"].children[0].current_reasoning
    ):
        print(step)
        print("---------")

    for step in (
        step_output.task_step.step_state["root_node"]
        .children[0]
        .children[0]
        .current_reasoning
    ):
        print(step)
        print("---------")

    
    # repeat until the last step is reached
    #while not step_output.is_last:
        #step_output = agent.run_step(task.task_id)

    # repeat until the last step is reached
    while not step_output.is_last:
        step_output = agent.run_step(task.task_id)

    response = agent.finalize_response(task.task_id)
    
    print(str(response))


    return response



if __name__ == "__main__":
    asyncio.run (query_agent())