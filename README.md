# fastapi_onazure

## Repository Overview
This repository provides the following features:

1. **RAG with LlamaIndex and Tree Agent**
   - Leverages LlamaIndex for fine-tuning Retrieval-Augmented Generation (RAG) with tree agent techniques.

2. **Installation and Run Instructions**
   - Step-by-step guide to set up and run the application locally or on Azure.

3. **Application Flow Diagram**
   - A flow chart that outlines the architecture and workflow of the application.

---

## Installation and Setup

### Prerequisites
- Python 3.12 (Python 3.13 is not compatible with `sentence-transformers`).
- Docker (optional for containerization).
- Azure CLI (for deployment on Azure).

### Steps to Install Libraries

1. **Create Virtual Environment:**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Required Libraries:**
   ```bash
   pip install "fastapi[all]"
   pip install sentence-transformers
   pip install llama-parse
   pip install llama-index-llms-openai
   pip install llama-index-llms-replicate
   pip install llama-index-embeddings-openai
   pip install llama-index-core llama-index-readers-file
   pip install llama-index-llms-ollama
   pip install llama-index-embeddings-huggingface
   pip install llama-index-vector-stores-weaviate
   pip install azure-storage-blob
   pip install langchain_community
   pip freeze > requirements.txt
   ```

### Running Locally

1. **Activate Virtual Environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Run the Application:**
   ```bash
   uvicorn app.main:app --port 8001
   ```
   - Default port: `8000`
   - Local URL: [http://localhost:8000](http://localhost:8000)

3. **Debugging Ports:**
   - Validate and kill hanging processes:
     ```bash
     ps aux | grep weaviate
     lsof -i :8000
     kill -9 <process_id>
     ```

### Docker Setup

#### Local Docker Build and Run
1. **Create Dockerfile and Build Image:**
   ```bash
   docker build -t ragimage .
   ```

2. **Run Container Locally:**
   ```bash
   docker run -d -p 80:80 -p 8000:8000 --name rag_container ragimage
   ```
   - To use local files in the container:
     ```bash
     docker run -d -p 80:80 -p 8000:8000 -v $(pwd):/code your_image_name
     ```

3. **Stop and Remove Container:**
   ```bash
   docker stop <container_id>
   docker rm <container_id>
   ```

4. **Vulnerability Report:**
   ```bash
   docker scout cves local://ragimage:latest
   ```

#### Azure Deployment
1. **Login to Azure Container Registry:**
   ```bash
   docker login <container_registry_server_name> -u <container_user_name> -p
   ```

2. **Build and Push Docker Image:**
   ```bash
   docker build --platform linux/amd64 -t ragcontainer.azurecr.io/<container_name>:<build_tag>
   docker push ragcontainer.azurecr.io/ragapi:<build_tag>
   ```

3. **Run App on Azure:**
   ```bash
   az deployment group operation list --resource-group rg-rag --name Microsoft.ContainerInstances-<timestamp>
   ```

---

## Application Flow Diagram
Below is a conceptual flow chart outlining the architecture and workflow of the application:

```
[User Query] --> [FastAPI Endpoint] --> [LlamaIndex RAG Engine] --> [Weaviate Vector Store] --> [Query Results]
```

---

## Additional Documentation

### Weaviate Embedded Documentation
- Ensure the embedded server runs without conflicts. Default ports:
  - HTTP: `8079`
  - gRPC: `50051`

### API Specifications
- Return objects and sample error objects are detailed in the API documentation.

### LlamaIndex Documentation
- For further details on LlamaIndex querying:
  [LlamaIndex Documentation](https://docs.llamaindex.ai/en/stable/understanding/querying/querying/)

---

## Notes
- Use Python 3.12 for compatibility with `sentence-transformers`.
- Replace `datetime.datetime.utcnow()` with timezone-aware objects like `datetime.datetime.now(datetime.UTC)` for compliance with `DeprecationWarning`.
