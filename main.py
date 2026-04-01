import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import requests
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno desde el archivo .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Cargar variables seguras
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
N8N_AUTH_TOKEN = os.getenv("N8N_AUTH_TOKEN")
N8N_AUTH_HEADER_NAME = os.getenv("N8N_AUTH_HEADER_NAME")

@app.get("/")
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/enviar-arco")
async def handle_form(
    request: Request,
    email: str = Form(...),
    tipo_derecho: str = Form(...),
    mensaje: str = Form(...)
):
    payload = {
        "email": email,
        "tipo_derecho": tipo_derecho,
        "mensaje": mensaje,
        "timestamp": datetime.now().isoformat() # Mejorado para enviar la fecha exacta actual
    }
    
    # Inyectar el Header de Autenticación
    headers = {
        N8N_AUTH_HEADER_NAME: N8N_AUTH_TOKEN
    }
    
    try:
        # Añadimos el parámetro headers a la petición
        response = requests.post(N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        
        # Si n8n responde con éxito
        if response.status_code == 200:
            return templates.TemplateResponse("success.html", {"request": request, "email": email})
        else:
            # Captura errores de autenticación (ej. 401 Unauthorized o 403 Forbidden)
            print(f"Error de n8n: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Error de validación en el servidor de destino.")
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"No se pudo conectar con el servidor: {str(e)}")