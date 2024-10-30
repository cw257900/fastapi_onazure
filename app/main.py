from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"use /prompt/'ask' to query our internal knowledge base"}

@app.get("/prompt/{ask}")
async def read_question (ask):
    return {"Prompt": {ask} }