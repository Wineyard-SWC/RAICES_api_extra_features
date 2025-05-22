from pydantic import BaseModel
from typing      import Optional

class SignInRequest(BaseModel):
    firebase_id: str
    name: str
    avatar_url: Optional[str] = None
    gender: Optional[str] = None
