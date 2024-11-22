
from llama_index import Prompt

text_qa_template = Prompt (
    "Context information is below. \n"
    "----------------------------- \n"
    "{context_str}\n"
    "----------------------------- \n"
    "Gvien the context information and not prior knowledge, "
    "answer the question: {query_str}"
)