# main.py

from fastapi import FastAPI
from app.routers import users, biometrics, sessions
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Ejemplo de API con FastAPI",
    description="API con rutas organizadas y conexión a SQL Server Express",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los routers
app.include_router(users.router)
app.include_router(biometrics.router)
app.include_router(sessions.router)  

# Ruta de prueba (raíz)
@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a la API con FastAPI y SQL Server Express!"}
