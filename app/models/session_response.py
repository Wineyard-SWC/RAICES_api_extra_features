from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class TaskResponse(BaseModel):
    task_id: str
    task_name: str
    normalized_stress: float
    emotion_label: str
    heart_rate: Optional[float]
    created_at: datetime

class BaselineResponse(BaseModel):
    baseline_eeg_theta_beta: Optional[float]
    baseline_hrv_lf_hf: Optional[float]
    baseline_hr: Optional[float]

class SessionResponse(BaseModel):
    session_id: str
    context_type: str
    created_at: datetime
    session_avg_stress: Optional[float]
    session_emotion: Optional[str]
    session_arousal: Optional[float]
    session_valence: Optional[float]
    
    # Información del usuario
    user_name: str
    user_avatar_url: Optional[str]
    user_firebase_id: str
    
    # Datos relacionados
    baseline: Optional[BaselineResponse]
    tasks: List[TaskResponse]

class SessionGroupResponse(BaseModel):
    session_relation: str
    total_participants: int
    sessions: List[SessionResponse]
    
    class Config:
        from_attributes = True