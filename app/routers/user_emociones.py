# app/routers/user_emociones.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app.db.connection import get_connection
from app.services.eeg_analysis import detect_emotion_from_eeg

router = APIRouter(
    prefix="/user-emociones",
    tags=["Usuario_Emociones"]
)

@router.post("/")
def asignar_emocion(usuario_id: int, emocion_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Usuario_Emociones (usuario_id, emocion_id)
            VALUES (?, ?);
        """, (usuario_id, emocion_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error al asignar emoción: {str(e)}")
    finally:
        conn.close()
    return {"message": "Emoción asignada exitosamente"}

@router.get("/{usuario_id}")
def get_emociones_de_usuario(usuario_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.emocion, ue.fecha_asignacion
        FROM Usuario_Emociones ue
        INNER JOIN Emociones e ON ue.emocion_id = e.id
        WHERE ue.usuario_id = ?
    """, (usuario_id,))
    rows = cursor.fetchall()
    conn.close()

    emociones = []
    for row in rows:
        emociones.append({
            "id": row[0],
            "emocion": row[1],
            "fecha_asignacion": row[2].isoformat() if row[2] else None
        })

    return {"usuario_id": usuario_id, "emociones": emociones}
