"use strict";

// Colores por clase (coinciden con el plan / paleta sobria)
const COLORES = {
  "Acacia negra": "#2f6db0",
  "Buchon de agua": "#2e7d5b",
  "Helecho de agua": "#8a6d1f",
  "Retamo espinoso": "#b5562a",
};
const COLOR_DEFECTO = "#5b6b7b";

// Estado
let imagenActual = null;   // File
let imgBitmap = null;      // HTMLImageElement cargada
let ultimoResultado = null;

// Refs
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const canvasWrap = document.getElementById("canvas-wrap");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const spinner = document.getElementById("spinner");
const controls = document.getElementById("controls");
const thr = document.getElementById("threshold");
const thrVal = document.getElementById("thr-val");
const btnOtra = document.getElementById("btn-otra");
const banner = document.getElementById("banner");
const porClase = document.getElementById("por-clase");
const listaDet = document.getElementById("lista-det");
const detCount = document.getElementById("det-count");
const estadoModelo = document.getElementById("estado-modelo");

// ---------- Health ----------
fetch("/api/health")
  .then((r) => r.json())
  .then((d) => {
    if (d.status === "ok") {
      estadoModelo.textContent = `RF-DETR · ${d.device}`;
      estadoModelo.className = "badge badge-ok";
    } else {
      estadoModelo.textContent = "cargando modelo…";
    }
  })
  .catch(() => {
    estadoModelo.textContent = "sin conexión";
    estadoModelo.className = "badge badge-err";
  });

// ---------- Drag & drop ----------
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
});
fileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files[0]) cargarImagen(e.target.files[0]);
});

["dragenter", "dragover"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);
dropzone.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files && e.dataTransfer.files[0];
  if (f) cargarImagen(f);
});

btnOtra.addEventListener("click", reset);

// Reenviar al cambiar el umbral
thr.addEventListener("input", () => { thrVal.textContent = parseFloat(thr.value).toFixed(2); });
thr.addEventListener("change", () => { if (imagenActual) analizar(); });

// ---------- Lógica ----------
function cargarImagen(file) {
  if (!file.type.startsWith("image/")) {
    mostrarError("El archivo no es una imagen.");
    return;
  }
  imagenActual = file;
  const img = new Image();
  img.onload = () => {
    imgBitmap = img;
    dropzone.hidden = true;
    canvasWrap.hidden = false;
    controls.hidden = false;
    dibujar([]);   // muestra la imagen sin cajas mientras analiza
    analizar();
  };
  img.onerror = () => mostrarError("No se pudo cargar la imagen.");
  img.src = URL.createObjectURL(file);
}

function analizar() {
  if (!imagenActual) return;
  spinner.hidden = false;

  const fd = new FormData();
  fd.append("imagen", imagenActual);
  fd.append("threshold", thr.value);

  fetch("/api/detect", { method: "POST", body: fd })
    .then(async (r) => {
      if (!r.ok) {
        const err = await r.json().catch(() => ({ detail: "Error del servidor." }));
        throw new Error(err.detail || "Error del servidor.");
      }
      return r.json();
    })
    .then((data) => {
      ultimoResultado = data;
      dibujar(data.detections);
      renderResultados(data);
    })
    .catch((e) => mostrarError(e.message))
    .finally(() => { spinner.hidden = true; });
}

function dibujar(detecciones) {
  if (!imgBitmap) return;
  const w = imgBitmap.naturalWidth;
  const h = imgBitmap.naturalHeight;
  canvas.width = w;
  canvas.height = h;
  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(imgBitmap, 0, 0, w, h);

  // grosor relativo al tamaño de la imagen
  const lw = Math.max(2, Math.round(Math.max(w, h) / 400));
  const fontSize = Math.max(14, Math.round(Math.max(w, h) / 45));
  ctx.lineWidth = lw;
  ctx.font = `600 ${fontSize}px -apple-system, "Segoe UI", Roboto, sans-serif`;
  ctx.textBaseline = "top";

  detecciones.forEach((d) => {
    const [x1, y1, x2, y2] = d.bbox;
    const color = COLORES[d.class_name] || COLOR_DEFECTO;
    ctx.strokeStyle = color;
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

    const label = `${d.class_name} ${d.confidence.toFixed(2)}`;
    const tw = ctx.measureText(label).width;
    const padX = fontSize * 0.3;
    const labelH = fontSize * 1.3;
    let ly = y1 - labelH;
    if (ly < 0) ly = y1; // si no cabe arriba, dibuja dentro
    ctx.fillStyle = color;
    ctx.fillRect(x1, ly, tw + padX * 2, labelH);
    ctx.fillStyle = "#fff";
    ctx.fillText(label, x1 + padX, ly + labelH * 0.13);
  });
}

function renderResultados(data) {
  const total = data.resumen.total;
  detCount.textContent = total;

  // Banner
  if (total === 0) {
    banner.className = "banner banner-ok";
    banner.textContent = "✓ No se detectaron especies invasoras.";
  } else {
    const nEspecies = Object.keys(data.resumen.por_clase).length;
    banner.className = "banner banner-warn";
    banner.textContent = `⚠ Invasión detectada: ${nEspecies} especie(s), ${total} detección(es).`;
  }

  // Conteo por clase
  porClase.innerHTML = "";
  const entradas = Object.entries(data.resumen.por_clase);
  if (entradas.length === 0) {
    porClase.innerHTML = '<li class="vacio">Ninguna</li>';
  } else {
    entradas
      .sort((a, b) => b[1] - a[1])
      .forEach(([nombre, n]) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <span class="clase-tag">
            <span class="dot" style="background:${COLORES[nombre] || COLOR_DEFECTO}"></span>${nombre}
          </span>
          <span class="pill-n">${n}</span>`;
        porClase.appendChild(li);
      });
  }

  // Lista de detecciones
  listaDet.innerHTML = "";
  if (total === 0) {
    listaDet.innerHTML = '<li class="vacio">Sin detecciones por encima del umbral.</li>';
  } else {
    data.detections.forEach((d) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <span class="clase-tag">
          <span class="dot" style="background:${COLORES[d.class_name] || COLOR_DEFECTO}"></span>${d.class_name}
        </span>
        <span class="conf">${(d.confidence * 100).toFixed(1)}%</span>`;
      listaDet.appendChild(li);
    });
  }
}

function mostrarError(msg) {
  banner.className = "banner banner-warn";
  banner.textContent = "Error: " + msg;
}

function reset() {
  imagenActual = null;
  imgBitmap = null;
  ultimoResultado = null;
  fileInput.value = "";
  canvasWrap.hidden = true;
  controls.hidden = true;
  dropzone.hidden = false;
  detCount.textContent = "0";
  banner.className = "banner banner-idle";
  banner.textContent = "Sube una imagen para detectar especies invasoras.";
  porClase.innerHTML = '<li class="vacio">—</li>';
  listaDet.innerHTML = '<li class="vacio">Aún no hay resultados.</li>';
}
