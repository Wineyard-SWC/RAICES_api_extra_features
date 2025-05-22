from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.userSignIn import SignInRequest
from app.models.avatar import AvatarUpdate

from app.db.connection import get_connection

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/signin")
def signin(user: SignInRequest):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (firebase_id, name, avatar_url, gender)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (firebase_id) DO NOTHING
            RETURNING id, created_at
            """,
            (user.firebase_id, user.name, user.avatar_url, user.gender),  # Usar user.gender en vez de None
        )
        row = cur.fetchone()

        if not row:
            cur.execute(
                "SELECT id, created_at FROM users WHERE firebase_id = %s",
                (user.firebase_id,),
            )
            row = cur.fetchone()
            
            # Verificar que se encontró el usuario
            if not row:
                raise HTTPException(status_code=404, detail="User with this firebase_id not found")

        new_id, created_at = row
        conn.commit()

    except Exception as e:
        conn.rollback()
        # Incluir el mensaje de error para mejor diagnóstico
        raise HTTPException(status_code=400, detail=f"Could not sign in user: {str(e)}")
    finally:
        cur.close()
        conn.close()

    return {"id": new_id, "created_at": created_at}

@router.get("/")
def get_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, firebase_id, name, avatar_url, gender, created_at
          FROM users
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id":     r[0],
            "firebase_id": r[1],
            "name":   r[2],
            "avatar_url":  r[3],
            "gender": r[4],
            "created_at":  r[5],
        }
        for r in rows
    ]

@router.get("/{user_id}")
def get_user(user_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, firebase_id, name, avatar_url, gender, created_at
          FROM users
         WHERE firebase_id = %s
        """,
        (user_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id":          row[0],
        "firebase_id": row[1],
        "name":        row[2],
        "avatar_url":  row[3],
        "gender":      row[4],
        "created_at":  row[5],
    }

@router.patch("/{user_id}/avatar", response_model=dict)
def update_avatar(user_id: str, payload: AvatarUpdate):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE users
               SET avatar_url = %s
             WHERE firebase_id = %s
            RETURNING firebase_id, avatar_url
            """,
            (payload.avatar_url, user_id)
        )
        row = cur.fetchone()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": row[0], "avatar_url": row[1]}

@router.patch("/{user_id}/profile", response_model=dict)
def update_profile(user_id: str, payload: AvatarUpdate):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Construir la consulta SQL dinámicamente basada en los campos proporcionados
        update_fields = []
        params = []
        
        if payload.avatar_url is not None:
            update_fields.append("avatar_url = %s")
            params.append(payload.avatar_url)
            
        if payload.gender is not None:
            update_fields.append("gender = %s")
            params.append(payload.gender)
            
        # Si no hay campos para actualizar, retornar
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        # Construir la consulta SQL
        sql = """
            UPDATE users
               SET {}
             WHERE firebase_id = %s
            RETURNING firebase_id, avatar_url, gender
            """.format(", ".join(update_fields))
        
        # Añadir el user_id a los parámetros
        params.append(user_id)
        
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": row[0], 
        "avatar_url": row[1], 
        "gender": row[2]
    }
