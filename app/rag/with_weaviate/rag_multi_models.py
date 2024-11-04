import time
import os
import sys
import base64
from sentence_transformers import SentenceTransformer
from PIL import Image
import pillow_avif
import pytesseract
import requests
import json
from pathlib import Path 
from weaviate.classes.query import MetadataQuery
import weaviate
import weaviate.classes as wvc
from weaviate.util import generate_uuid5

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vector_stores import vector_stores 
from configs import configs

from dotenv import load_dotenv
load_dotenv()

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

import logging
logging.basicConfig(level=logging.ERROR)


image_path = os.getenv("LOCAL_INPUT_PATH_IMAGE")
class_name = configs.WEAVIATE_STORE_NAME
class_description = configs.WEAVIATE_STORE_DESCRIPTION

client = vector_stores.create_client()
collection = client.collections.get(class_name)

#https://huggingface.com/sentence-transformers/ 
img_model = SentenceTransformer('clip-Vit-B-32')
text_model = SentenceTransformer('sentence-transformers/clip-ViT-B-32-multilingual-v1')


counter = 0
start_time = time.time()

def load_image(image_path):
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return Image.open(requests.get(image_path, stream=True).raw)
    else:
        return Image.open(image_path)

def to_base64(path):
    with open(path, 'rb') as file:
        return base64.base64encode(file.read()).decode('utf-8')

def load_image_matplot(image_path):
    """Loads an image from a file path."""
    return mpimg.imread(image_path)

def extract_text_from_image(image_path):
    """Extracts text from an image using OCR."""
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

# Example usage:
#src_image_path = "path/to/src_image.jpg"
#additional_image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
def show_images(src_image=None, image_paths=[]):

    # Load images from provided paths
    images = [load_image(path) for path in image_paths]

    # Extract text for each image path as metadata
    metadata = [extract_text_from_image(path) for path in image_paths]

    
    # Add src_image to the beginning if provided
    if src_image:
        images = [load_image(src_image)] + images
        metadata = [extract_text_from_image(src_image)] + metadata
        
    
    # Display images in a row
    _, axs = plt.subplots(1, len(images), figsize=(20, 10))
    for i, img in enumerate(images):
        axs[i].imshow(img)
        axs[i].axis('off')  # Turn off axis for each image
        axs[i].set_title(metadata[i], fontsize=8)
    
    plt.show()

# upsert images from a directory, skip  duplicate
def upsert_to_vectorstore(client, image_path = image_path):
   
    collection =  client.collections.get(class_name )
    counter = 0
    
    start_time = time.time()
    with collection.batch.dynamic() as batch :

        file_paths = [f for f in Path(image_path).iterdir() if f.is_file()]

        for file_path in file_paths :

            counter +=1

            try:
                print (" == image file " , file_path)
                image= Image.open(file_path)
                metadata = pytesseract.image_to_string(image)
                vector = img_model.encode(image).tolist()

                with open(file_path, 'rb') as file:
                    img_b64 = base64.b64encode(file.read()).decode('utf-8')

                # Insert single object
                data_object={
                        "source": str(image_path),
                        "image_file": str(file_path),
                        "image": img_b64,
                        "image_content": metadata
                }

                collection.data.insert(
                        properties=data_object,
                        vector=vector,  # Include if vector is required
                        # uuid=generate_uuid5(image_path),
                )

                
                
                vector_dimension = len(vector)
                print(" == Image Inserted, embedding dimension:", vector_dimension)
                print()
            
            except Exception as e :
                print(f"Error processing {file_path}: {e}")
                print()
                continue

    print (" == total images: " , counter)
    vector_stores.close_client (client)

        
def queries (collection, client, query):
    #query = "Can you find my receipt with date 01/16/1968?"
    
    query_vector = text_model.encode([query])[0].tolist() 


    response = collection.query.near_vector (
       near_vector = query_vector,
       return_properties=[ "image", "image_file"],
       
       limit=2
    )
        
    return response
       

def parse_query_result(query, client, class_name):

    print ("image path" , image_path)

    collection = client.collections.get(class_name)
    #image_paths = [os.path.join(image_path, filename) for filename in os.listdir(image_path) if filename.endswith((".jpg", ".jpeg", ".png"))]
    #show_images( image_paths=image_paths)
    #upsert_to_vectorstore(client, image_path=image_path)
    response =queries (collection, client, query)
    
     # Assuming `obj` is your object 
    obj = response.objects[0] 
    image_file = obj.properties.get('image_file')
    image = obj.properties.get('image')

    # Display images in a row
    fig, axs = plt.subplots(1, len(response.objects), figsize=(15, 5))  # Create a row of subplots

    for idx, obj in enumerate(response.objects):
        image_file = obj.properties.get('image_file')
        print(f" === Image File Path {idx+1}:", image_file)

        # Check if the image file path exists
        if image_file and os.path.isfile(image_file):
            # Load and display the image
            image = Image.open(image_file)
            axs[idx].imshow(image)
            axs[idx].axis('off')  # Turn off axis for each image
        else:
            print(f"No valid image file found for object {idx+1}")

    plt.show()
    print (" query result ", MetadataQuery(distance=True))

    vector_stores.close_client(client)

if __name__ == "__main__": 
    print ("image path" , image_path)
    client = vector_stores.create_client()
    collection = client.collections.get(class_name)
    #image_paths = [os.path.join(image_path, filename) for filename in os.listdir(image_path) if filename.endswith((".jpg", ".jpeg", ".png"))]
    #show_images( image_paths=image_paths)
    
    #upsert_to_vectorstore(client, image_path=image_path)

    # query = "Can you find a picture of crowd street?"
    query = "crowd"
    parse_query_result(query, client, class_name)