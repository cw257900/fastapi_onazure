from pydantic import BaseModel

class Metadata(BaseModel):
    conversation_id: str
    user_id: str
    pdf_id: str

    model_config = {
        "extra": "forbid"  # You can use "allow", "ignore", or "forbid"
    }


class ChatArgs(BaseModel):
    conversation_id: str
    pdf_id: str
    metadata: Metadata
    streaming: bool
    
    model_config = {
        "extra": "forbid"  # You can use "allow", "ignore", or "forbid"
    }

