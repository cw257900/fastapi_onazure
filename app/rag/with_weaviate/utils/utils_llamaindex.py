import re
import fitz  # PyMuPDF for PDF parsing
from llama_index.core import Document

def dynamic_format_text(text):
    # Replace escaped newlines and normalize spacing
    text = text.replace("\\n", "\n").replace("  ", " ")
    
    # Split text into lines and initialize formatted output
    lines = text.splitlines()
    formatted_text = ""
    
    for line in lines:
        # Strip any excess spaces from the line
        stripped_line = line.strip()

        # Detect paragraphs (non-empty lines that aren’t headers)
        if stripped_line:
            # If the last character of formatted text is not a space or newline, add space for continuity
            if formatted_text and formatted_text[-1] not in "\n ":
                formatted_text += " "
            formatted_text += stripped_line
        
        # Add blank line for paragraph breaks when there’s an empty line
        else:
            formatted_text += "\n"

    # Replace multiple newlines with two (for section separation)
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text).strip()
    
    return formatted_text

#not used
def parse_pdf_with_page_numbers(file_path):
    documents = []
    pdf = fitz.open(file_path)  # Open the PDF

    for page_num in range(pdf.page_count):
        page = pdf[page_num]
        text = page.get_text()
        metadata = {
            "page_number": page_num + 1  # Add page number to metadata
        }
        documents.append(Document(text=text, metadata=metadata))

    pdf.close()
    return documents


# configure response synthesizer with a custom handler for metadata
def get_response_with_metadata(response):
    # Iterate through each result and include page number
    results = []
    
    for node in response.source_nodes:
        
        page_number = node.metadata.get('page_number')  # get page number from metadata
        text = node.text
        results.append(f"(Page {page_number}): {text}")
        
    return node.metadata, "\n".join(results)
