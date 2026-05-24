# RF-DETR demo para Hugging Face Spaces

Este repositorio está preparado para desplegar la web app en **Hugging Face Spaces** usando **Docker**.

## Incluye

- `Dockerfile` para Spaces.
- `checkpoint_best_regular.pth` como modelo entrenado.
- `webapp/` con la API FastAPI y el frontend estático.

## Variables clave

- `RFDETR_CKPT=/app/checkpoint_best_regular.pth`
- `PORT=7860`

## Build local

```bash
docker build -t plantas-invasoras-hf .
docker run -p 7860:7860 plantas-invasoras-hf
```

## Push a Spaces

1. Inicia sesión en Hugging Face.
2. Crea un Space con SDK `Docker`.
3. Sube este repositorio con Git LFS habilitado para `*.pth`.
