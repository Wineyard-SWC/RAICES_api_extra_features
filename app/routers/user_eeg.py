from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app.db.connection import get_connection
from app.services.eeg_analysis import detect_emotion_from_eeg 

router = APIRouter(
    prefix="/user_eeg",
    tags=["Usuario_EEG"]
)

# Modelo para encapsular la data recibida en el body
class EEGDataRequest(BaseModel):
    usuario_id: int
    eeg_data: List[Dict[str, Any]]

@router.post("/")
def create_emotion_from_eeg(payload: EEGDataRequest):
    """
    Recibe el ID de un usuario y un array JSON con lecturas EEG.
    Procesa los datos para determinar la emoción y la inserta en la tabla intermedia.
    """
    usuario_id = payload.usuario_id
    eeg_data = payload.eeg_data

    if not eeg_data:
        raise HTTPException(status_code=400, detail="No se recibió data EEG")

    # 1) Detectar emoción (solo usaremos el nombre, no el emoji)
    emotion, _ = detect_emotion_from_eeg(eeg_data)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 2) Verificar si la emoción ya existe en la tabla Emociones
        cursor.execute("SELECT id FROM Emociones WHERE emocion = ?;", (emotion,))
        row = cursor.fetchone()

        if row:
            emocion_id = row[0]
        else:
            # Si no existe, insertar la emoción en la tabla Emociones
            cursor.execute("INSERT INTO Emociones (emocion) OUTPUT Inserted.id VALUES (?);", (emotion,))
            emocion_id = cursor.fetchone()[0]

        # 3) Insertar en Usuario_Emociones
        cursor.execute("""
            INSERT INTO Usuario_Emociones (usuario_id, emocion_id)
            VALUES (?, ?);
        """, (usuario_id, emocion_id))
        conn.commit()

        return {
            "message": "Emoción registrada exitosamente.",
            "usuario_id": usuario_id,
            "emocion": emotion
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al asignar emoción: {str(e)}")
    finally:
        conn.close()