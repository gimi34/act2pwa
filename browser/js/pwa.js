/* Núcleo · PWA: registra el service worker, muestra el botón de instalar y avisa cuando no hay internet. */
(function () {
  "use strict";

  /* ---------- Registro del service worker ---------- */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("sw.js", { scope: "./" }).catch(function () {});
    });
  }

  /* ---------- Aviso (conexión e instrucciones) ---------- */
  var aviso = document.getElementById("aviso-red");
  var texto = document.getElementById("aviso-red-texto");
  var temporizador = null;

  function mostrarAviso(mensaje, correcto, milisegundos) {
    if (!aviso) { return; }
    clearTimeout(temporizador);
    aviso.classList.toggle("aviso-ok", !!correcto);
    texto.textContent = mensaje;
    aviso.hidden = false;
    if (milisegundos) {
      temporizador = setTimeout(function () { aviso.hidden = true; }, milisegundos);
    }
  }

  function sinConexion() {
    document.documentElement.classList.add("sin-red");
    mostrarAviso("Sin conexión a internet. Estás viendo la copia guardada.", false, 0);
  }

  function conConexion() {
    document.documentElement.classList.remove("sin-red");
    if (!aviso || aviso.hidden) { return; }
    mostrarAviso("Conexión restablecida.", true, 3000);
  }

  window.addEventListener("offline", sinConexion);
  window.addEventListener("online", conConexion);
  if (!navigator.onLine) { sinConexion(); }

  /* ---------- Botón «Instalar app» ---------- */
  var boton = document.getElementById("pwa-instalar");
  var solicitud = null;

  // Si ya se abrió como app instalada (ventana propia), el botón no hace falta.
  function yaInstalada() {
    return navigator.standalone === true ||
      ["standalone", "fullscreen", "minimal-ui"].some(function (modo) {
        return window.matchMedia("(display-mode: " + modo + ")").matches;
      });
  }

  if (boton && !yaInstalada()) { boton.hidden = false; }

  // Chrome, Edge y Android avisan que la app se puede instalar: guardamos ese aviso.
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    solicitud = e;
    if (boton) { boton.hidden = false; }
  });

  if (boton) {
    boton.addEventListener("click", function () {
      if (solicitud) {
        solicitud.prompt();
        solicitud.userChoice.then(function () { solicitud = null; });
        return;
      }
      // El navegador no ofreció su ventana de instalación (iPhone, Firefox o modo browser):
      // explicamos cómo instalar desde su menú.
      var esIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) ||
        (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
      mostrarAviso(esIOS
        ? "Para instalar: toca Compartir y luego «Agregar a pantalla de inicio»."
        : "Para instalar: abre el menú ⋮ del navegador y elige «Instalar app» o «Agregar a pantalla principal».",
        true, 7000);
    });
  }

  window.addEventListener("appinstalled", function () {
    solicitud = null;
    if (boton) { boton.hidden = true; }
    mostrarAviso("App instalada. Ábrela desde su icono.", true, 4000);
  });
})();
