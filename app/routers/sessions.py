from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from typing import List

from app.db.async_engine import get_async_db
from app.db.models_bio import Session, User, SessionTask, Baseline
from app.models.session_response import SessionGroupResponse, SessionResponse, TaskResponse, BaselineResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("/by-relation/{session_relation}", response_model=SessionGroupResponse)
async def get_sessions_by_relation(
    session_relation: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene todas las sesiones agrupadas por session_relation
    con información completa de usuarios y tareas
    """
    try:
        # Query con joins para obtener toda la información necesaria
        stmt = (
            select(Session)
            .options(
                joinedload(Session.user),
                joinedload(Session.tasks),
                joinedload(Session.baselines)
            )
            .join(User)
            .where(Session.session_relation == session_relation)
            .order_by(Session.created_at)
        )
        
        result = await db.execute(stmt)
        sessions = result.scalars().unique().all()
        
        if not sessions:
            raise HTTPException(
                status_code=404, 
                detail=f"No sessions found for relation: {session_relation}"
            )
        
        # Construir respuesta
        session_responses = []
        
        for session in sessions:
            # Baseline (tomar el primero si existe)
            baseline_data = None
            if session.baselines:
                baseline = session.baselines[0]
                baseline_data = BaselineResponse(
                    baseline_eeg_theta_beta=float(baseline.baseline_eeg_theta_beta) if baseline.baseline_eeg_theta_beta else None,
                    baseline_hrv_lf_hf=float(baseline.baseline_hrv_lf_hf) if baseline.baseline_hrv_lf_hf else None,
                    baseline_hr=float(baseline.baseline_hr) if baseline.baseline_hr else None
                )
            
            # Tasks
            task_responses = [
                TaskResponse(
                    task_id=task.task_id,
                    task_name=task.task_name,
                    normalized_stress=float(task.normalized_stress),
                    emotion_label=task.emotion_label,
                    heart_rate=float(task.heart_rate) if task.heart_rate else None,
                    created_at=task.created_at
                )
                for task in session.tasks
            ]
            
            # Session completa
            session_response = SessionResponse(
                session_id=session.session_id,
                context_type=session.context_type,
                created_at=session.created_at,
                session_avg_stress=float(session.session_avg_stress) if session.session_avg_stress else None,
                session_emotion=session.session_emotion,
                session_arousal=float(session.session_arousal) if session.session_arousal else None,
                session_valence=float(session.session_valence) if session.session_valence else None,
                
                # Usuario info
                user_name=session.user.name,
                user_avatar_url=session.user.avatar_url,
                user_firebase_id=session.user.firebase_id,
                
                # Datos relacionados
                baseline=baseline_data,
                tasks=task_responses
            )
            
            session_responses.append(session_response)
        
        return SessionGroupResponse(
            session_relation=session_relation,
            total_participants=len(session_responses),
            sessions=session_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{firebase_id}", response_model=List[SessionResponse])
async def get_user_sessions(
    firebase_id: str,
    project_id: str = None,  # ✅ Parámetro opcional para filtrar por proyecto
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene todas las sesiones de un usuario específico, opcionalmente filtradas por proyecto
    """
    try:
        # ✅ Query básico para todas las sesiones del usuario
        stmt = (
            select(Session)
            .options(
                joinedload(Session.user),
                joinedload(Session.tasks),
                joinedload(Session.baselines)
            )
            .join(User)
            .where(Session.user_firebase_id == firebase_id)
            .order_by(Session.created_at.desc())
        )
        
        result = await db.execute(stmt)
        all_sessions = result.scalars().unique().all()
        
        if not all_sessions:
            raise HTTPException(
                status_code=404, 
                detail=f"No sessions found for user: {firebase_id}"
            )
        
        # ✅ Filtrar por proyecto si se proporciona project_id
        filtered_sessions = []
        
        for session in all_sessions:
            # Extraer project_id del session_id
            # Formato: session_timestamp_projectId_userId
            session_parts = session.session_id.split('_')
            
            if len(session_parts) >= 4:  # session_timestamp_projectId_userId
                session_project_id = session_parts[2]
                
                # Si no se especifica project_id, incluir todas las sesiones
                # Si se especifica, solo incluir las que coincidan
                if project_id is None or session_project_id == project_id:
                    filtered_sessions.append(session)
            else:
                # Si el formato no coincide, incluir solo si no se filtra por proyecto
                if project_id is None:
                    filtered_sessions.append(session)
        
        if not filtered_sessions:
            project_msg = f" for project: {project_id}" if project_id else ""
            raise HTTPException(
                status_code=404, 
                detail=f"No sessions found for user: {firebase_id}{project_msg}"
            )
        
        # ✅ Construir respuesta
        session_responses = []
        
        for session in filtered_sessions:
            baseline_data = None
            if session.baselines:
                baseline = session.baselines[0]
                baseline_data = BaselineResponse(
                    baseline_eeg_theta_beta=float(baseline.baseline_eeg_theta_beta) if baseline.baseline_eeg_theta_beta else None,
                    baseline_hrv_lf_hf=float(baseline.baseline_hrv_lf_hf) if baseline.baseline_hrv_lf_hf else None,
                    baseline_hr=float(baseline.baseline_hr) if baseline.baseline_hr else None
                )
            
            task_responses = [
                TaskResponse(
                    task_id=task.task_id,
                    task_name=task.task_name,
                    normalized_stress=float(task.normalized_stress),
                    emotion_label=task.emotion_label,
                    heart_rate=float(task.heart_rate) if task.heart_rate else None,
                    created_at=task.created_at
                )
                for task in session.tasks
            ]
            
            session_response = SessionResponse(
                session_id=session.session_id,
                context_type=session.context_type,
                created_at=session.created_at,
                session_avg_stress=float(session.session_avg_stress) if session.session_avg_stress else None,
                session_emotion=session.session_emotion,
                session_arousal=float(session.session_arousal) if session.session_arousal else None,
                session_valence=float(session.session_valence) if session.session_valence else None,
                
                user_name=session.user.name,
                user_avatar_url=session.user.avatar_url,
                user_firebase_id=session.user.firebase_id,
                
                baseline=baseline_data,
                tasks=task_responses
            )
            
            session_responses.append(session_response)
        
        return session_responses
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching user sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")