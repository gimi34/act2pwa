#!/usr/bin/env python3
"""Genera las cuatro versiones PWA de la página (una carpeta por modo display).

Uso (desde la carpeta act2):   python3 herramientas/generar_pwa.py

Cada carpeta (browser/, minimal-ui/, standalone/, fullscreen/) queda completa e
independiente: su propio index.html, manifest.json, sw.js (service worker), caché e
iconos. La página original de la raíz NO se modifica; se copia.

Para cambiar la orientación de una versión, edita la tabla VERSIONES y vuelve a ejecutar.
"""
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración: display + orientation de cada integrante
# ---------------------------------------------------------------------------
VERSIONES = [
    # carpeta        display        orientation  nombre corto
    ("browser",     "browser",     "any",       "Núcleo Browser"),
    ("minimal-ui",  "minimal-ui",  "portrait",  "Núcleo Minimal"),
    ("standalone",  "standalone",  "portrait",  "Núcleo Standalone"),
    ("fullscreen",  "fullscreen",  "landscape", "Núcleo Fullscreen"),
]
VERSION_CACHE = "v3"  # súbelo (v2, v3…) cada vez que cambies archivos para renovar la caché
COLOR_TEMA = "#0A1424"
COLOR_FONDO = "#0A1424"

RAIZ = Path(__file__).resolve().parent.parent
CARPETAS_COPIADAS = ["css", "fonts", "img", "js", "vendor"]

# ---------------------------------------------------------------------------
# Plantillas
# ---------------------------------------------------------------------------
SW = """/* Service worker de la versión «{display}» · orientation «{orientation}».
   Estrategia: precache de todos los archivos al instalar (Cache Storage) y
   «cache first» al pedir recursos, con respaldo a la red. Así la PWA funciona sin conexión. */
const CACHE = "nucleo-{carpeta}-{version}";
const ARCHIVOS = {archivos};

// 1) Instalación: guarda todos los archivos en Cache Storage.
self.addEventListener("install", (evento) => {{
  evento.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ARCHIVOS)).then(() => self.skipWaiting())
  );
}});

// 2) Activación: borra cachés viejas de ESTA versión y toma control de la página.
self.addEventListener("activate", (evento) => {{
  evento.waitUntil(
    caches.keys().then((claves) => Promise.all(
      claves
        .filter((clave) => clave.startsWith("nucleo-{carpeta}-") && clave !== CACHE)
        .map((clave) => caches.delete(clave))
    )).then(() => self.clients.claim())
  );
}});

// 3) Peticiones: primero la caché; si no está, la red (y se guarda copia).
self.addEventListener("fetch", (evento) => {{
  const peticion = evento.request;
  if (peticion.method !== "GET" || new URL(peticion.url).origin !== self.location.origin) {{
    return;
  }}
  // manifest.json: primero la red, para que un cambio de display/orientation llegue al teléfono.
  if (new URL(peticion.url).pathname.endsWith("/manifest.json")) {{
    evento.respondWith(
      fetch(peticion).then((respuesta) => {{
        const copia = respuesta.clone();
        caches.open(CACHE).then((cache) => cache.put(peticion, copia));
        return respuesta;
      }}).catch(() => caches.match(peticion))
    );
    return;
  }}
  evento.respondWith(
    caches.match(peticion, {{ ignoreSearch: true }}).then((enCache) => {{
      if (enCache) {{ return enCache; }}
      return fetch(peticion).then((respuesta) => {{
        if (respuesta.ok) {{
          const copia = respuesta.clone();
          caches.open(CACHE).then((cache) => cache.put(peticion, copia));
        }}
        return respuesta;
      }}).catch(() => {{
        // Sin conexión y sin copia: si es una página, mostramos index.html.
        if (peticion.mode === "navigate") {{ return caches.match("./index.html"); }}
        return Response.error();
      }});
    }})
  );
}});
"""

PWA_JS = r"""/* Núcleo · PWA: registra el service worker y avisa cuando no hay internet. */
(function () {
  "use strict";

  /* ---------- Registro del service worker ---------- */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("sw.js", { scope: "./" }).catch(function () {});
    });
  }

  /* ---------- Aviso de conexión ---------- */
  var aviso = document.getElementById("aviso-red");
  var texto = document.getElementById("aviso-red-texto");
  var temporizador = null;

  function sinConexion() {
    if (!aviso) { return; }
    clearTimeout(temporizador);
    aviso.classList.remove("aviso-ok");
    texto.textContent = "Sin conexión a internet. Estás viendo la copia guardada.";
    aviso.hidden = false;
  }

  function conConexion() {
    if (!aviso || aviso.hidden) { return; }
    aviso.classList.add("aviso-ok");
    texto.textContent = "Conexión restablecida.";
    clearTimeout(temporizador);
    temporizador = setTimeout(function () { aviso.hidden = true; }, 3000);
  }

  window.addEventListener("offline", sinConexion);
  window.addEventListener("online", conConexion);
  if (!navigator.onLine) { sinConexion(); }
})();
"""

PWA_CSS = """/* Núcleo · aviso de conexión (igual en las cuatro versiones). Usa los tokens de estilos.css. */
.aviso-red {
  position: fixed;
  left: 50%;
  bottom: var(--space-4);
  transform: translateX(-50%);
  z-index: 50;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: max-content;
  max-width: calc(100% - 2 * var(--space-4));
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border-left: var(--space-1) solid var(--color-primary);
  background: var(--color-night);
  color: var(--color-on-night);
  font-size: var(--text-small);
  font-weight: 600;
  box-shadow: 0 0.5rem 1.5rem rgba(10, 20, 36, 0.35);
}
.aviso-red[hidden] { display: none; }
.aviso-red i { color: var(--color-primary); }
.aviso-red.aviso-ok { border-left-color: var(--color-success); }
.aviso-red.aviso-ok i { color: #6FD39B; }
"""

FICHA_HTML = """  <div id="aviso-red" class="aviso-red" role="status" aria-live="polite" hidden>
    <i class="fa-solid fa-wifi" aria-hidden="true"></i>
    <span id="aviso-red-texto"></span>
  </div>
"""

HEAD_EXTRA = """  <link rel="manifest" href="manifest.json">
  <meta name="theme-color" content="{tema}">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="{corto}">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
  <link rel="stylesheet" href="css/pwa.css">
  <script src="js/pwa.js" defer></script>
"""


# ---------------------------------------------------------------------------
def generar_iconos(destino: Path):
    """Crea los PNG del manifest a partir de img/favicon.svg."""
    from PIL import Image

    destino.mkdir(parents=True, exist_ok=True)
    svg = RAIZ / "img" / "favicon.svg"
    base = Path(tempfile.gettempdir()) / "nucleo_base.png"
    subprocess.run(["convert", "-background", "none", "-density", "1200", str(svg),
                    "-resize", "512x512", str(base)], check=True)
    logo = Image.open(base).convert("RGBA")

    for tam in (192, 512):
        logo.resize((tam, tam), Image.LANCZOS).save(destino / f"icon-{tam}.png")

    # Maskable: logo al 70 % sobre fondo naranja completo (zona segura del 80 %).
    fondo = Image.new("RGBA", (512, 512), "#FF6A13")
    peq = logo.resize((358, 358), Image.LANCZOS)
    fondo.alpha_composite(peq, ((512 - 358) // 2, (512 - 358) // 2))
    fondo.save(destino / "maskable-512.png")

    # iOS no admite transparencia en el icono.
    ios = Image.new("RGBA", (180, 180), "#FF6A13")
    ios.alpha_composite(logo.resize((180, 180), Image.LANCZOS))
    ios.convert("RGB").save(destino / "apple-touch-icon.png")


def generar_version(carpeta, display, orientation, corto):
    dest = RAIZ / carpeta
    dest.mkdir(exist_ok=True)

    for sub in CARPETAS_COPIADAS:
        shutil.copytree(RAIZ / sub, dest / sub, dirs_exist_ok=True)

    generar_iconos(dest / "icons")
    (dest / "css" / "pwa.css").write_text(PWA_CSS, encoding="utf-8")
    (dest / "js" / "pwa.js").write_text(PWA_JS, encoding="utf-8")

    # index.html: el original + manifest/meta en <head> + aviso de conexión tras el encabezado.
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    html = html.replace("<title>Núcleo · Qué hay dentro de una computadora</title>",
                        f"<title>Núcleo · PWA {display}</title>", 1)
    extra = HEAD_EXTRA.format(tema=COLOR_TEMA, corto=corto)
    html = html.replace('  <script src="js/app.js" defer></script>\n',
                        '  <script src="js/app.js" defer></script>\n' + extra, 1)
    html = html.replace("  </header>\n\n  <main", "  </header>\n\n"
                        + FICHA_HTML.format(display=display, orientation=orientation)
                        + "\n  <main", 1)
    assert 'rel="manifest"' in html and "aviso-red" in html, "no se pudo insertar en index.html"
    (dest / "index.html").write_text(html, encoding="utf-8")

    manifest = {
        "id": "./",
        "name": f"Núcleo · PWA {display} ({orientation})",
        "short_name": corto,
        "description": "Guía sobre computadoras: componentes, tipos, historia y qué equipo conviene según tu uso.",
        "lang": "es",
        "dir": "ltr",
        "start_url": "./",
        "scope": "./",
        "display": display,
        "orientation": orientation,
        "theme_color": COLOR_TEMA,
        "background_color": COLOR_FONDO,
        "categories": ["education"],
        "icons": [
            {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")

    # Lista de archivos a precachear (todo lo de la carpeta salvo el propio sw.js).
    archivos = ["./"] + sorted(
        "./" + p.relative_to(dest).as_posix()
        for p in dest.rglob("*")
        if p.is_file() and p.name not in ("sw.js",) and not p.name.startswith((".", "_"))
        and not p.name.startswith("LICENSE")
    )
    (dest / "sw.js").write_text(SW.format(display=display, orientation=orientation, carpeta=carpeta,
                                          version=VERSION_CACHE,
                                          archivos=json.dumps(archivos, ensure_ascii=False, indent=2)),
                                encoding="utf-8")
    print(f"✓ {carpeta}/  display={display}  orientation={orientation}  ({len(archivos)} archivos en caché)")


if __name__ == "__main__":
    for v in VERSIONES:
        generar_version(*v)
