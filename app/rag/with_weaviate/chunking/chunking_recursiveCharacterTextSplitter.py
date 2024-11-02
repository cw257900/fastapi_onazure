import os
import sys 
import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter,RecursiveCharacterTextSplitter


# Add the parent directory (or wherever "with_pinecone" is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configs import configs


load_dotenv()

def replace_newlines_in_docs(docs):
    for doc in docs:
        doc.page_content = doc.page_content.replace('\n', ' ')
    return docs

# Function to split the extracted text into chunks for better embedding
def get_chunked_doc(pdf_file_path):
    try: 
        if not pdf_file_path or not os.path.exists(pdf_file_path):
            raise ValueError(f"Invalid PDF file path: {pdf_file_path}")
        
        # Load the PDF
        docs = PyPDFLoader(pdf_file_path)

        # Define the text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=5000,
            chunk_overlap=300,
            length_function=len,
            separators=["\n\n", "\n", ".", "?", "!"]
        )
        
        # Load and split the documents
        docs = docs.load_and_split(text_splitter)
        
        # Replace '\n' with space in the split documents
        docs = replace_newlines_in_docs(docs)

        print("chunking_recursiveCharacterTextSplitter.py: file is being chunked: ", pdf_file_path)
        
        return docs

    except Exception as e:
        print(f"Error from {pdf_file_path}: {e}")
        raise

    finally :
        None

def main ():
 
    pdf_file_path =  os.getenv("LOCAL_FILE_INPUT_PATH")
    doc = get_chunked_doc(pdf_file_path)
    print(f"001. Number of chunks from pdf: {len(doc)}")


if __name__ == "__main__":
    main()