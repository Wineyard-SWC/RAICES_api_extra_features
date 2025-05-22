# # app/routers/emociones.py

# from fastapi import APIRouter, HTTPException
# from app.db.connection import get_connection

# router = APIRouter(
#     prefix="/emociones",
#     tags=["Emociones"]
# )

# @router.get("/")
# def get_emociones():
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT id, emocion FROM Emociones")
#     rows = cursor.fetchall()
#     conn.close()

#     emociones = []
#     for row in rows:
#         emociones.append({"id": row[0], "emocion": row[1]})
#     return {"emociones": emociones}

# @router.post("/")
# def create_emocion(emocion: str):
#     conn = get_connection()
#     cursor = conn.cursor()
#     try:
#         cursor.execute("INSERT INTO Emociones (emocion) VALUES (?);", (emocion,))
#         conn.commit()
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=400, detail=f"Error al crear emoción: {str(e)}")
#     finally:
#         conn.close()
#     return {"message": "Emoción creada con éxito"}

# @router.delete("/{emocion_id}")
# def delete_emocion(emocion_id: int):
#     """
#     Elimina una emoción de la base de datos por su ID.
#     """
#     conn = get_connection()
#     cursor = conn.cursor()
#     try:
#         cursor.execute("DELETE FROM Emociones WHERE id = ?;", (emocion_id,))
#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="Emoción no encontrada")
#         conn.commit()
#         return {"message": f"Emoción con ID {emocion_id} eliminada exitosamente"}
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=500, detail=f"Error al eliminar emoción: {str(e)}")
#     finally:
#         conn.close()
