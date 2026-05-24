"""
Web app FastAPI para detección de plantas invasoras con RF-DETR.

Sirve la API (`/api/detect`, `/api/health`) y el frontend estático. El modelo se carga una
sola vez al arrancar y corre en la GPU (AMD/ROCm) si está disponible. Las imágenes se procesan
en memoria y NO se persisten.

Ejecutar:
    .\\.venv-rocm\\Scripts\\python.exe -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import io
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from webapp.detector import PlantDetector

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BYTES = 15 * 1024 * 1024  # 15 MB
# Formatos válidos (se valida decodificando con PIL; el content-type es solo informativo)
FORMATOS_OK = {"JPEG", "PNG", "WEBP"}

# Estado del server (modelo + lock para serializar la GPU)
estado: dict = {"detector": None, "device": "desconocido"}
gpu_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Carga el modelo al arrancar (bloqueante; aceptable, es el arranque)
    try:
        import torch

        estado["device"] = (
            torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
        )
    except Exception:
        estado["device"] = "desconocido"

    estado["detector"] = PlantDetector()
    yield
    estado["detector"] = None


app = FastAPI(title="Detección de plantas invasoras — RF-DETR", lifespan=lifespan)

# CORS abierto para que funcione detrás del túnel (Cloudflare/ngrok)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    det: PlantDetector | None = estado["detector"]
    if det is None:
        return JSONResponse({"status": "cargando"}, status_code=503)
    return {
        "status": "ok",
        "device": estado["device"],
        "modelo": "RF-DETR",
        "checkpoint": det.checkpoint.name,
        "clases": det.nombres_invasoras,
    }


@app.post("/api/detect")
async def detect(
    imagen: UploadFile = File(...),
    threshold: float = Form(0.3),
):
    det: PlantDetector | None = estado["detector"]
    if det is None:
        raise HTTPException(status_code=503, detail="El modelo aún se está cargando.")

    data = await imagen.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="La imagen supera el límite de 15 MB.")
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacío.")

    try:
        pil = Image.open(io.BytesIO(data))
        pil.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="No se pudo leer la imagen.")

    if pil.format not in FORMATOS_OK:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado ({pil.format}). Usa JPG, PNG o WEBP.",
        )

    threshold = max(0.01, min(0.99, float(threshold)))

    # Una sola GPU: serializar las inferencias
    async with gpu_lock:
        try:
            resultado = await run_in_threadpool(det.detect, pil, threshold)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Error en la inferencia: {e}")

    return resultado


# Estáticos (CSS/JS) — se monta al final para no tapar las rutas de la API
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
