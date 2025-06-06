from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, Text, ForeignKey, func
)
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    firebase_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    gender = Column(String)
    
    # ✅ Relación hacia Sessions
    sessions = relationship("Session", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"

    session_id         = Column(String(500), primary_key=True)
    user_firebase_id   = Column(String(255),
                                ForeignKey("users.firebase_id",
                                           ondelete="CASCADE"))
    context_type       = Column(String(30),  nullable=False)
    created_at         = Column(DateTime,    server_default=func.now())
    session_avg_stress = Column(Numeric(4, 3))
    session_emotion    = Column(String(30))
    session_arousal    = Column(Numeric(5, 3))
    session_valence    = Column(Numeric(5, 3))
    session_relation   = Column(String(50))

    user = relationship("User", back_populates="sessions")

    tasks     = relationship("SessionTask", back_populates="session",
                             cascade="all, delete")
    baselines = relationship("Baseline",    back_populates="session",
                             cascade="all, delete")
    

class Baseline(Base):
    __tablename__ = 'baselines'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.session_id'), nullable=False)  # ← CLAVE FORÁNEA
    baseline_eeg_theta_beta = Column(Numeric(5, 3))
    baseline_hrv_lf_hf = Column(Numeric(5, 3))
    baseline_hr = Column(Numeric(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación hacia Session (opcional)
    session = relationship("Session", back_populates="baselines")


class SessionTask(Base):
    __tablename__ = "session_tasks"

    id                = Column(Integer, primary_key=True)
    session_id        = Column(String(500),
                               ForeignKey("sessions.session_id",
                                          ondelete="CASCADE"))
    task_id           = Column(String(50), nullable=False)
    task_name         = Column(String(200), nullable=False)
    normalized_stress = Column(Numeric(4, 3), nullable=False)
    emotion_label     = Column(String(30),   nullable=False)
    heart_rate        = Column(Numeric(5, 2))  # ✅ Nueva columna para HR
    readings_file     = Column(Text)
    created_at        = Column(DateTime, server_default=func.now())

    session = relationship("Session", back_populates="tasks")
