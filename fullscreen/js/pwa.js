/* Núcleo · PWA: registra el service worker y avisa cuando no hay internet. */
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
