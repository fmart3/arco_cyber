from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# URL de tu Webhook de n8n (Cópiala de tu nodo Webhook1)
N8N_WEBHOOK_URL = "https://pepelagos.app.n8n.cloud/webhook/arco-cybertrust"

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
        "timestamp": "2026-03-09" # Dato útil para trazabilidad
    }
    
    # Enviar a n8n
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        
        # Si n8n responde con éxito
        if response.status_code == 200:
            return templates.TemplateResponse("success.html", {
                "request": request, 
                "email": email
            })
        else:
            return f"Error en el motor de automatización: {response.status_code}"

    except requests.exceptions.ConnectionError:
        return "Error: No se pudo conectar con n8n. ¿Está encendido?"