# Detección de plantas invasoras 🌿

Proyecto universitario de visión por computador para **detectar especies de plantas
invasoras en Cundinamarca, Colombia** a partir de imágenes.

## Propósito

Las plantas invasoras desplazan a las especies nativas y afectan los ecosistemas.
Este proyecto entrena modelos de detección de objetos capaces de **identificar y
localizar** automáticamente 4 especies invasoras en una foto:

- Acacia negra
- Buchón de agua
- Helecho de agua
- Retamo espinoso

El objetivo es **comparar de forma justa** tres arquitecturas de detección
—**RT-DETR**, **RF-DETR**— entrenadas sobre el mismo conjunto de datos
y evaluadas sobre las mismas imágenes, para determinar cuál funciona mejor en este
caso real.

## Cómo funciona

1. Las imágenes se anotan y exportan desde Roboflow (formatos COCO y YOLO).
2. Un proceso de preparación construye los datasets y fija una división común de
   entrenamiento/validación, igual para todos los modelos.
3. Se entrena cada modelo mediante *transfer learning* (a partir de pesos
   preentrenados) sobre GPU local.
4. Se comparan los resultados con las mismas métricas (mAP, precisión, recall).

## Resultados (RF-DETR)

| Métrica   | Valor |
| ---------- | ----- |
| mAP@50     | 0.64  |
| Precisión | 0.83  |
| Recall     | 0.54  |

## Demo web

Incluye una aplicación web sencilla (`webapp/`) para arrastrar una imagen y ver las
detecciones en el navegador, usando el mejor modelo RF-DETR del proyecto.

---

> Proyecto académico. Código, comentarios y documentación en español.
