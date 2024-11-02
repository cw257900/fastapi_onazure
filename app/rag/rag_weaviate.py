import sys
import os
import json

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import with_weaviate.vectordb_retrieve as retrive 
import with_weaviate.vectordb_create as upload 


def load_to_vectorstore ():
    upload.upsert_chunks_to_store(pdf_file_path, vector_store, class_name) 
    None

# Function to build index over data file
def rag_retrieval (prompt, limit=1):

    json_list = []
    print (" = 2.0 rag asking ", prompt)
    hybrid_rlt = retrive.query(prompt, limit=limit)

    print (" = 2.0 rag answer ", hybrid_rlt)

    idx =0
    for o in hybrid_rlt.objects:
        """
        print(" = 2. rag ", idx)
        print(" = 2. rag page_content ", o.properties.get("page_content"))
        print(" = 2. rag score ", o.metadata.score)
        print(" = 2. rag explain_score ", o.metadata.explain_score)
        idx =idx+1
        print()
        """
        
        json_object = {
            "page_content": o.properties.get("page_content"),
            "page_number": o.properties.get("page_number"),
            "source": o.properties.get("source"),
            "score": o.metadata.score,
            "explain_score": str(o.metadata.explain_score).replace("\n", "")
        }
    
        json_list.append(json_object)

    return json_list
    


if __name__ =="__main__" :
    prompt = "sumerize the insurance document"
    rag_retrieval(prompt)