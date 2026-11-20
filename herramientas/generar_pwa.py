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
VERSION_CACHE = "v2"  # súbelo (v2, v3…) cada vez que cambies archivos para renovar la caché
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

PWA_JS = r"""/* Núcleo · PWA: registra el service worker y muestra la ficha de la versión.
   No fuerza ninguna orientación: solo informa lo que declara el manifest
   y lo que el dispositivo está haciendo realmente. */
(function () {
  "use strict";

  /* ---------- Registro del service worker ---------- */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("sw.js", { scope: "./" }).then(function () {
        poner("pwa-sw", "activo");
      }).catch(function () {
        poner("pwa-sw", "error al registrar");
      });
    });
  } else {
    poner("pwa-sw-dd", null);
  }

  function poner(id, texto) {
    var el = document.getElementById(id);
    if (el && texto !== null) { el.textContent = texto; }
  }

  /* ---------- Valores declarados en manifest.json ---------- */
  var enlace = document.querySelector('link[rel="manifest"]');
  if (enlace && window.fetch) {
    fetch(enlace.href).then(function (r) { return r.json(); }).then(function (m) {
      poner("pwa-display", m.display || "—");
      poner("pwa-orientation", m.orientation || "—");
    }).catch(function () {});
  }

  /* ---------- Modo de visualización real ---------- */
  var modos = ["fullscreen", "standalone", "minimal-ui", "browser"];
  function modoActual() {
    for (var i = 0; i < modos.length; i++) {
      if (window.matchMedia("(display-mode: " + modos[i] + ")").matches) { return modos[i]; }
    }
    return navigator.standalone ? "standalone" : "browser";
  }
  function actualizarModo() { poner("pwa-modo", modoActual()); }
  modos.forEach(function (m) {
    var mq = window.matchMedia("(display-mode: " + m + ")");
    if (mq.addEventListener) { mq.addEventListener("change", actualizarModo); }
  });
  actualizarModo();

  /* ---------- Orientación real de la pantalla ---------- */
  function orientacionActual() {
    if (screen.orientation && screen.orientation.type) {
      return screen.orientation.type.indexOf("portrait") === 0 ? "vertical (portrait)" : "horizontal (landscape)";
    }
    return window.matchMedia("(orientation: portrait)").matches ? "vertical (portrait)" : "horizontal (landscape)";
  }
  function actualizarOrientacion() { poner("pwa-giro", orientacionActual()); }
  if (screen.orientation && screen.orientation.addEventListener) {
    screen.orientation.addEventListener("change", actualizarOrientacion);
  }
  window.addEventListener("resize", actualizarOrientacion);
  actualizarOrientacion();

  /* ---------- Conexión ---------- */
  function actualizarRed() {
    var enLinea = navigator.onLine;
    poner("pwa-red", enLinea ? "en línea" : "sin conexión (desde caché)");
    document.documentElement.classList.toggle("sin-red", !enLinea);
  }
  window.addEventListener("online", actualizarRed);
  window.addEventListener("offline", actualizarRed);
  actualizarRed();

  /* ---------- Botón de instalación (Chrome / Edge / Android) ---------- */
  var aviso = null;
  var boton = document.getElementById("pwa-instalar");
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    aviso = e;
    if (boton) { boton.hidden = false; }
  });
  if (boton) {
    boton.addEventListener("click", function () {
      if (!aviso) { return; }
      aviso.prompt();
      aviso.userChoice.then(function () { aviso = null; boton.hidden = true; });
    });
  }
  window.addEventListener("appinstalled", function () {
    if (boton) { boton.hidden = true; }
    poner("pwa-modo", modoActual() + " · instalada");
  });
})();
"""

PWA_CSS = """/* Núcleo · ficha PWA (igual en las cuatro versiones). Usa los tokens de estilos.css. */
.ficha-pwa {
  background: var(--color-night);
  color: var(--color-on-night);
  border-bottom: var(--space-1) solid var(--color-primary);
  font-size: var(--text-small);
}
.ficha-pwa-interior {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-5);
  padding-block: var(--space-3);
}
.ficha-pwa dl { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-5); margin: 0; }
.ficha-pwa dl div { display: flex; gap: var(--space-2); align-items: baseline; }
.ficha-pwa dt { color: var(--color-on-night-muted); font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.04em; }
.ficha-pwa dd { margin: 0; font-weight: 600; }
.ficha-pwa .declarado { color: var(--color-primary); font-family: var(--font-mono); }
.ficha-pwa .boton-instalar {
  min-height: var(--touch-min);
  padding-inline: var(--space-4);
  border: 0;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.ficha-pwa .boton-instalar[hidden] { display: none; }
.ficha-pwa :focus-visible { outline: 3px solid var(--color-focus-on-night); outline-offset: 2px; }
.sin-red .ficha-pwa { border-bottom-color: var(--color-focus-on-night); }
"""

FICHA_HTML = """  <section class="ficha-pwa" aria-label="Datos de esta versión PWA">
    <div class="contenedor ficha-pwa-interior">
      <dl>
        <div><dt>display</dt><dd class="declarado" id="pwa-display">{display}</dd></div>
        <div><dt>orientation</dt><dd class="declarado" id="pwa-orientation">{orientation}</dd></div>
        <div><dt>Modo actual</dt><dd id="pwa-modo">—</dd></div>
        <div><dt>Pantalla</dt><dd id="pwa-giro">—</dd></div>
        <div><dt>Conexión</dt><dd id="pwa-red">—</dd></div>
        <div id="pwa-sw-dd"><dt>Service worker</dt><dd id="pwa-sw">—</dd></div>
      </dl>
      <button id="pwa-instalar" class="boton-instalar" type="button" hidden>
        <i class="fa-solid fa-download" aria-hidden="true"></i> Instalar app
      </button>
    </div>
  </section>
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

    # index.html: el original + manifest/meta en <head> + ficha PWA tras el encabezado.
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    html = html.replace("<title>Núcleo · Qué hay dentro de una computadora</title>",
                        f"<title>Núcleo · PWA {display}</title>", 1)
    extra = HEAD_EXTRA.format(tema=COLOR_TEMA, corto=corto)
    html = html.replace('  <script src="js/app.js" defer></script>\n',
                        '  <script src="js/app.js" defer></script>\n' + extra, 1)
    html = html.replace("  </header>\n\n  <main", "  </header>\n\n"
                        + FICHA_HTML.format(display=display, orientation=orientation)
                        + "\n  <main", 1)
    assert 'rel="manifest"' in html and "ficha-pwa" in html, "no se pudo insertar en index.html"
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
