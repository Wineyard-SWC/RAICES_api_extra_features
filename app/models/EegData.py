from pydantic import BaseModel
from typing import List, Dict, Any

class EegDataRequest(BaseModel):
    usuario_id: int
    eeg_data: List[Dict[str, Any]]
