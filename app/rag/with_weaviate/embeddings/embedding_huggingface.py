from sentence_transformers import SentenceTransformer
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

# Usage
chosen_model = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=chosen_model)

# Embed a single query
# dimension 384
query_embedding = embeddings.embed_query("Sample query text")
#print("Query Embedding Dimension:", len(query_embedding))

# Embed multiple documents
docs = ["First document to embed", "Second document to embed"]
doc_embeddings = embeddings.embed_documents(docs)
#print("Document Embeddings:", doc_embeddings)

