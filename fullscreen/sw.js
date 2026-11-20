/* Service worker de la versión «fullscreen» · orientation «landscape».
   Estrategia: precache de todos los archivos al instalar (Cache Storage) y
   «cache first» al pedir recursos, con respaldo a la red. Así la PWA funciona sin conexión. */
const CACHE = "nucleo-fullscreen-v3";
const ARCHIVOS = [
  "./",
  "./css/estilos.css",
  "./css/pwa.css",
  "./fonts/ibm-plex-mono-latin-500-normal.woff2",
  "./fonts/ibm-plex-sans-latin-400-normal.woff2",
  "./fonts/ibm-plex-sans-latin-600-normal.woff2",
  "./fonts/ibm-plex-sans-latin-700-normal.woff2",
  "./icons/apple-touch-icon.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/maskable-512.png",
  "./img/almacenamiento.webp",
  "./img/favicon.svg",
  "./img/fuente-poder.webp",
  "./img/memoria-ram.webp",
  "./img/placa-base.webp",
  "./img/procesador.webp",
  "./img/tarjeta-grafica.webp",
  "./img/tipo-escritorio.webp",
  "./img/tipo-mini-pc.webp",
  "./img/tipo-portatil.webp",
  "./img/tipo-todo-en-uno.webp",
  "./index.html",
  "./js/app.js",
  "./js/pwa.js",
  "./manifest.json",
  "./vendor/fontawesome/css/all.min.css",
  "./vendor/fontawesome/webfonts/fa-brands-400.woff2",
  "./vendor/fontawesome/webfonts/fa-regular-400.woff2",
  "./vendor/fontawesome/webfonts/fa-solid-900.woff2",
  "./vendor/fontawesome/webfonts/fa-v4compatibility.woff2"
];

// 1) Instalación: guarda todos los archivos en Cache Storage.
self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ARCHIVOS)).then(() => self.skipWaiting())
  );
});

// 2) Activación: borra cachés viejas de ESTA versión y toma control de la página.
self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((claves) => Promise.all(
      claves
        .filter((clave) => clave.startsWith("nucleo-fullscreen-") && clave !== CACHE)
        .map((clave) => caches.delete(clave))
    )).then(() => self.clients.claim())
  );
});

// 3) Peticiones: primero la caché; si no está, la red (y se guarda copia).
self.addEventListener("fetch", (evento) => {
  const peticion = evento.request;
  if (peticion.method !== "GET" || new URL(peticion.url).origin !== self.location.origin) {
    return;
  }
  // manifest.json: primero la red, para que un cambio de display/orientation llegue al teléfono.
  if (new URL(peticion.url).pathname.endsWith("/manifest.json")) {
    evento.respondWith(
      fetch(peticion).then((respuesta) => {
        const copia = respuesta.clone();
        caches.open(CACHE).then((cache) => cache.put(peticion, copia));
        return respuesta;
      }).catch(() => caches.match(peticion))
    );
    return;
  }
  evento.respondWith(
    caches.match(peticion, { ignoreSearch: true }).then((enCache) => {
      if (enCache) { return enCache; }
      return fetch(peticion).then((respuesta) => {
        if (respuesta.ok) {
          const copia = respuesta.clone();
          caches.open(CACHE).then((cache) => cache.put(peticion, copia));
        }
        return respuesta;
      }).catch(() => {
        // Sin conexión y sin copia: si es una página, mostramos index.html.
        if (peticion.mode === "navigate") { return caches.match("./index.html"); }
        return Response.error();
      });
    })
  );
});
