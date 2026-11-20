/* Núcleo · PWA: registra el service worker y muestra la ficha de la versión.
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
