# app/routers/users.py

from fastapi import APIRouter, HTTPException
from app.db.connection import get_connection

router = APIRouter(
    prefix="/users",
    tags=["Users"]  # etiqueta para la documentación de Swagger
)

@router.get("/")
def get_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, avatar_url, fecha_creacion FROM Usuarios")
    rows = cursor.fetchall()
    conn.close()

    # Convertimos cada fila en un diccionario
    users = []
    for row in rows:
        users.append({
            "id": row[0],
            "nombre": row[1],
            "avatar_url": row[2],
            "fecha_creacion": row[3].isoformat() if row[3] else None
        })

    return {"users": users}

@router.post("/")
def create_user(id_firebase: str, nombre: str, avatar_url: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Usuarios (id_firebase, nombre, avatar_url)
            VALUES (?, ?, ?);
        """, (id_firebase, nombre, avatar_url))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear usuario: {str(e)}")
    finally:
        conn.close()

    return {"message": "Usuario creado con éxito"}
