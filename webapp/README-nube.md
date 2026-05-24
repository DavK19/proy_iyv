# Desplegar la web app de detección de plantas invasoras (RF-DETR) en la nube

Este paquete contiene el front + el modelo RF-DETR ya entrenado. La inferencia
detecta 4 especies invasoras: **Acacia negra, Buchon de agua, Helecho de agua,
Retamo espinoso**.

## Contenido del paquete

```
checkpoint_best_regular.pth   <- el modelo entrenado (122 MB)
_annotations.coco.json        <- nombres de las clases (opcional)
webapp/
  app.py                      <- servidor FastAPI
  detector.py                 <- carga el modelo y corre inferencia
  requirements-nube.txt       <- dependencias para la nube
  static/                     <- la página web (HTML/CSS/JS)
```

## 1. Ubicar el modelo

El código busca el checkpoint en la ruta relativa
`runs/rfdetr/exp2_neg020/checkpoint_best_regular.pth`. Tienes dos opciones:

**Opción A** — recrear esa ruta:
```bash
mkdir -p runs/rfdetr/exp2_neg020
mv checkpoint_best_regular.pth runs/rfdetr/exp2_neg020/
```

**Opción B** — dejar el `.pth` donde quieras y apuntarlo con una variable de entorno:
```bash
export RFDETR_CKPT=/ruta/a/checkpoint_best_regular.pth
```

(El `_annotations.coco.json` solo se usa para los nombres de clase; si lo pones en
`data_rfdetr/train/` se lee automáticamente. Si no está, el código usa las 4 clases
por defecto, así que es opcional.)

## 2. Instalar dependencias

> NO instales el PyTorch ROCm de Windows. En la nube usa el build CUDA o CPU.

```bash
python -m venv venv
source venv/bin/activate

# GPU NVIDIA:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
# (o solo CPU): pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

pip install -r webapp/requirements-nube.txt
```

## 3. Arrancar el servidor

Desde la **raíz del proyecto** (la carpeta que contiene `webapp/`):

```bash
uvicorn webapp.app:app --host 0.0.0.0 --port 8000
```

El modelo se carga al arrancar (tarda unos segundos). Luego abre
`http://<ip-del-servidor>:8000`.

## Endpoints

- `GET /` — la página web.
- `GET /api/health` — estado, GPU detectada y clases.
- `POST /api/detect` — `multipart/form-data` con `imagen` (archivo) y `threshold` (0–1).
  Devuelve JSON con `width`, `height`, `detections[]` y `resumen`.

## Notas

- La resolución de inferencia es **448** (fija, debe coincidir con el entrenamiento).
- `num_classes=5` en el modelo (4 invasoras + 1 fondo); el front solo muestra las 4 invasoras.
- Las imágenes se procesan en memoria y no se guardan.
- En despliegue real, ponle un reverse proxy (nginx/Caddy) o el HTTPS del proveedor delante.
