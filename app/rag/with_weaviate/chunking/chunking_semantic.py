para = """
 Traveling down a gravelly road in West Orange, New Jersey, an electric car sped by pedestrians, some clearly surprised by the vehicle's roomy interior. It travelled at twice the speed of the more conventional vehicles it overtook, stirring up dust that perhaps tickled the noses of the horses pulling carriages steadily along the street.

It was the early 1900s, and the driver of this particular car was Thomas Edison. While electric cars weren't a novelty in the neighborhood, most of them relied on heavy and cumbersome lead-acid batteries. Edison had outfitted his car with a new type of battery that he hoped would soon be powering vehicles throughout the country: a nickel-iron battery. Building on the work of the Swedish inventor Ernst Waldemar Jungner, who first patented a nickel-iron battery in 1899, Edison sought to refine the battery for use in automobiles.

Edison claimed the nickel-iron battery was incredibly resilient, and could be charged twice as fast as lead-acid batteries. He even had a deal in place with Ford Motors to produce this purportedly more efficient electric vehicle. 

"""
import re

from langchain.embeddings import  HuggingFaceEmbeddings



def split_para_to_sentence(para):
    sentences = re.split(r'(?<=[.!?])\s+', para)
    print(sentences)
    print()

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print (embeddings)


    return sentences


def create_semantic_chunks(sentences):
    sen_embeddings = [embedings.embed_query(sentence) for sentence in sentences]    
    print(sen_embeddings)






