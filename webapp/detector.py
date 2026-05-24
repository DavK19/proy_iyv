"""
Inferencia RF-DETR para la web app.

Envuelve `RFDETRBase` (paquete rfdetr) y expone un método `detect()` simple que recibe una
imagen PIL y devuelve las detecciones de las 4 especies invasoras. Reutiliza el mismo patrón
de la celda 6.1 del notebook (`entrenamiento_plantas.ipynb`).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from PIL import Image

# Raíz del proyecto (un nivel arriba de webapp/)
ROOT = Path(__file__).resolve().parent.parent

# Checkpoint por defecto: el respaldo del mejor modelo (Exp 2, neg 0.20). Configurable por env.
CKPT_DEFECTO = ROOT / "runs" / "rfdetr" / "exp2_neg020" / "checkpoint_best_regular.pth"

# Mapeo fijo de clases (orden fijo del proyecto). La 5 es fondo y casi nunca aparece.
CLASES_FIJAS = {
    1: "Acacia negra",
    2: "Buchon de agua",
    3: "Helecho de agua",
    4: "Retamo espinoso",
    5: "sin_invasion",
}

# Las 4 especies invasoras reales (lo único que se muestra como detección). El COCO de
# Roboflow además trae una categoría placeholder ("Object-Detection") y el fondo
# ("sin_invasion"), que se descartan.
INVASORAS = ("Acacia negra", "Buchon de agua", "Helecho de agua", "Retamo espinoso")

# Resolución de entrenamiento — debe coincidir.
RESOLUCION = 448


class PlantDetector:
    """Carga el modelo RF-DETR una vez y corre inferencia sobre imágenes PIL."""

    def __init__(self, checkpoint: str | os.PathLike | None = None):
        from rfdetr import RFDETRBase  # import perezoso: pesado y solo necesario en el server

        ruta_ckpt = Path(checkpoint or os.environ.get("RFDETR_CKPT") or CKPT_DEFECTO)
        if not ruta_ckpt.exists():
            raise FileNotFoundError(
                f"No se encontró el checkpoint RF-DETR en {ruta_ckpt}. "
                "Define RFDETR_CKPT o entrena el modelo."
            )
        self.checkpoint = ruta_ckpt
        self.clases = self._cargar_clases()
        self.model = RFDETRBase(
            pretrain_weights=str(ruta_ckpt),
            num_classes=5,
            resolution=RESOLUCION,
        )
        self._warmup()

    def _cargar_clases(self) -> dict[int, str]:
        """Lee los nombres del COCO derivado si existe (como el notebook); si no, los fijos."""
        coco = ROOT / "data_rfdetr" / "train" / "_annotations.coco.json"
        try:
            cats = json.load(open(coco, encoding="utf-8"))["categories"]
            mapa = {int(c["id"]): c["name"] for c in cats}
            return mapa or dict(CLASES_FIJAS)
        except Exception:
            return dict(CLASES_FIJAS)

    @property
    def nombres_invasoras(self) -> list[str]:
        """Las 4 clases invasoras reales (excluye fondo y placeholders)."""
        return list(INVASORAS)

    def _warmup(self) -> None:
        """Una inferencia dummy para que la primera petición real no pague la carga en frío."""
        try:
            dummy = Image.new("RGB", (RESOLUCION, RESOLUCION), (0, 0, 0))
            self.model.predict(dummy, threshold=0.5)
        except Exception:
            # El warmup es best-effort; si falla, la primera petición real lo hará.
            pass

    def detect(self, imagen: Image.Image, threshold: float = 0.3) -> dict:
        """
        Corre inferencia sobre una imagen PIL.

        Devuelve un dict con:
          - width, height: dimensiones de la imagen original (px)
          - threshold: umbral aplicado
          - detections: lista de {class_id, class_name, confidence, bbox:[x1,y1,x2,y2]}
          - resumen: {total, por_clase: {clase: n}}
        bbox en píxeles de la imagen original.
        """
        imagen = imagen.convert("RGB")
        w, h = imagen.size
        det = self.model.predict(imagen, threshold=float(threshold))

        detecciones: list[dict] = []
        por_clase: dict[str, int] = {}
        for cid, conf, box in zip(det.class_id, det.confidence, det.xyxy):
            cid = int(cid)
            nombre = self.clases.get(cid, str(cid))
            if nombre not in INVASORAS:
                continue  # fondo (sin_invasion) o placeholder (Object-Detection)
            x1, y1, x2, y2 = (float(v) for v in box)
            detecciones.append(
                {
                    "class_id": cid,
                    "class_name": nombre,
                    "confidence": float(conf),
                    "bbox": [x1, y1, x2, y2],
                }
            )
            por_clase[nombre] = por_clase.get(nombre, 0) + 1

        # Ordenar por confianza descendente
        detecciones.sort(key=lambda d: d["confidence"], reverse=True)

        return {
            "width": w,
            "height": h,
            "threshold": float(threshold),
            "detections": detecciones,
            "resumen": {"total": len(detecciones), "por_clase": por_clase},
        }
