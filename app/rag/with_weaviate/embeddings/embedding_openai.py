
import os
import sys
from langchain_openai import OpenAIEmbeddings 

# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configs import configs
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
chosen_model = "text-embedding-ada-002" # this is also OPENAI's default model

# Set API keys and Weaviate URL from environment variables
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model=chosen_model)

sample_text = "try to get model's dimension"
dimension=len(embeddings.embed_query(sample_text))

print(f" == 0.1. embeddings initiated from embedding_openai.py: {chosen_model}  and dimension: {dimension}")
print()

