from typing import List, Literal, Optional
from pydantic import BaseModel, validator

EEGChannel = Literal["TP9", "AF7", "AF8", "TP10"]

class ChannelPacket(BaseModel):
    channel: EEGChannel
    values: List[float]

class RestData(BaseModel):
    eeg: List[ChannelPacket]
    ppg: Optional[List[Optional[float]]] = None   # permite None internos
    hr:  Optional[List[Optional[float]]] = None

    # → Filtramos antes de la validación de tipo
    @validator("ppg", "hr", pre=True)
    def clean_numeric_list(cls, v):
        if v is None:
            return []            # campo omitido o null → lista vacía
        if isinstance(v, list):
            return [x for x in v if x is not None]
        raise TypeError("ppg/hr must be list or null")

class TaskPacket(BaseModel):
    taskId:      str
    taskName:    str
    userRating:  int
    explanation: Optional[str] = None
    eeg: List[ChannelPacket]
    ppg: Optional[List[Optional[float]]] = None
    hr:  Optional[List[Optional[float]]] = None

    @validator("ppg", "hr", pre=True)
    def clean_numeric_list(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [x for x in v if x is not None]
        raise TypeError("ppg/hr must be list or null")

class SessionPayload(BaseModel):
    sessionId:      str
    userFirebaseId: str
    participantId:  str
    contextType:    Literal["task_evaluation", "meeting", "calibration"]
    sessionRelation: Optional[str] = None
    restData:       RestData
    tasks:          List[TaskPacket]
