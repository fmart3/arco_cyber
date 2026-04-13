import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware # NUEVO: Previene el 405
import httpx # NUEVO: Evita que el servidor se congele
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# 🛡️ PROTECCIÓN CORS: Indispensable para portales públicos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cuando lo integres al sitio oficial, pon el dominio aquí
    allow_credentials=True,
    allow_methods=["*"], # Permite POST, GET y OPTIONS
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET")

@app.get("/")
async def read_form(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/enviar-arco")
async def redirect_to_home():
    return RedirectResponse(url="/")

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
        "timestamp": datetime.now().isoformat()
    }
    
    headers = {
        "Authorization": f"Bearer {N8N_WEBHOOK_SECRET}",
        "Content-Type": "application/json"
    }
    
    # 🚀 LLAMADA ASÍNCRONA: Evita el colapso del servidor en Render
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=15.0)
            
            # n8n puede devolver 200, 201 o 202 dependiendo del nodo
            if response.status_code in (200, 201, 202):
                try:
                    data = response.json()
                except ValueError:
                    data = {}
                
                if data.get("status") == "consent_email_sent":
                    return templates.TemplateResponse(request=request, name="success.html", context={
                        "email": email,
                        "mensaje_especial": "Hemos pausado su solicitud. Le enviamos un correo para validar su autorización de privacidad. Una vez aceptado, vuelva a enviar este formulario."
                    })
                else:
                    return templates.TemplateResponse(request=request, name="success.html", context={
                        "email": email,
                        "mensaje_especial": None
                    })
            else:
                print(f"Error de n8n: {response.status_code} - {response.text}")
                raise HTTPException(status_code=502, detail="Error de comunicación con nuestro Agente de Privacidad.")
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail="Servicio temporalmente no disponible. Intente en unos minutos.")