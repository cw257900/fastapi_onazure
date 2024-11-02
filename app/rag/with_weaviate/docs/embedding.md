
# Embedding Strategy

#### Pre-Embedded Vector Approach

Where to do the Embedding:
1. Pre-embed vectors before loading to Weaviate, or 
2. Use [Weaviate embed](https://weaviate.io/developers/weaviate/concepts/vector-quantization) during object creation. 

What models to use:
1. openai: text2vec_openai
    - text-embedding-3-large, dimensions: 3072 
    - text-embedding-3-small,dimensions: 1536 
    - availale model names: ada babbage curie davinci text-embedding-3-small text-embedding-3-large
2. cohere: text2vec-cohere
    - available module name: [command-r-plus command-r command-xlarge-beta command-xlarge command-medium command-xlarge-nightly command-medium-nightly xlarge medium command command-light command-nightly command-light-nightly base base-light]
3. huggingface: dimention=384, segments=192, 128, 96 ; use transformer models such as BERT, GPT:
    - text2vec-transformers/all-MiniLM-L12-v2:  
            Slightly larger version of MiniLM-L6, providing higher accuracy at the cost of performance.
    - sentence-transformers/all-MiniLM-L6-v2: 
            Small, efficient model for sentence embeddings.
    - sentence-transformers/paraphrase-MiniLM-L6-v2: 
            Optimized for paraphrase detection and similar sentence tasks.
    - sentence-transformers/paraphrase-mpnet-base-v2: 
            High-quality model for paraphrase detection, offering more accuracy than MiniLM models.
    - distilbert-base-uncased
            Distilled version of BERT, smaller and faster while retaining much of BERT’s accuracy.
    - bert-base-uncased
            The original BERT model, widely used for various NLP tasks.
    - roberta-base
            A variation of BERT, fine-tuned for robustness in various tasks.
    - sentence-transformers/stsb-roberta-base-v2
            RoBERTa model fine-tuned for the STS benchmark.
    - sentence-transformers/multi-qa-MiniLM-L6-cos-v1
            A multi-lingual model optimized for question-answering tasks.
    - sentence-transformers/msmarco-MiniLM-L6-cos-v5
            A model optimized for document retrieval tasks, such as in search engines.
            
            ........



4. Image-based Embedding: img2vec-neural
    - convert images to venctor embedding using neura network models; useful in multimedia search and image-based similarity queries

Used in Solution: 
```
    Weaviate to embed: text2vec-openai text-embedding-3-small, dimensions: 1536, max token 8191
    vectorizer_config=
            wvc.config.Configure.Vectorizer.text2vec_openai(
                model="text-embedding-ada-002",
                name="page_content",
                source_properties="page_content"
            ),    # Set the vectorizer to "text2vec-openai" to use the OpenAI API for vector-related operations
            generative_config=wvc.config.Configure.Generative.cohere(
                name="tiles", 
                source="page_content"
            ),             
```

sentence token -> semantic embedding -> vector db