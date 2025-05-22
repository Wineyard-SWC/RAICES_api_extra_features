# app/models/avatar.py
from pydantic import BaseModel
from typing import Optional

class AvatarUpdate(BaseModel):
    avatar_url: Optional[str] = None
    gender: Optional[str] = None
