/* Núcleo · comportamiento de la página.
   Sin red, sin almacenamiento del navegador y sin insertar HTML: todo texto entra con textContent. */
(function () {
  "use strict";

  var raiz = document.documentElement;
  raiz.classList.add("js");

  /* ---------- Menú móvil ---------- */
  var botonMenu = document.querySelector(".menu-boton");
  var menu = document.getElementById("menu-principal");

  function cambiarMenu(abrir) {
    if (!botonMenu || !menu) { return; }
    menu.classList.toggle("abierto", abrir);
    botonMenu.setAttribute("aria-expanded", abrir ? "true" : "false");
  }

  if (botonMenu && menu) {
    botonMenu.addEventListener("click", function () {
      cambiarMenu(botonMenu.getAttribute("aria-expanded") !== "true");
    });
    menu.addEventListener("click", function (e) {
      if (e.target.closest("a")) { cambiarMenu(false); }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && botonMenu.getAttribute("aria-expanded") === "true") {
        cambiarMenu(false);
        botonMenu.focus();
      }
    });
  }

  /* ---------- Tarjetas: "Ver más" ---------- */
  document.querySelectorAll(".ver-mas").forEach(function (boton) {
    boton.addEventListener("click", function () {
      var abierto = boton.getAttribute("aria-expanded") === "true";
      var panel = document.getElementById(boton.getAttribute("aria-controls"));
      boton.setAttribute("aria-expanded", abierto ? "false" : "true");
      if (panel) { panel.hidden = abierto; }
      var texto = boton.querySelector(".ver-mas-texto");
      if (texto) { texto.textContent = abierto ? "Ver más" : "Ver menos"; }
    });
  });

  /* ---------- Pestañas: tipos de computadoras ---------- */
  var pestanas = Array.prototype.slice.call(document.querySelectorAll("#tipos [role=tab]"));

  function elegirPestana(indice, enfocar) {
    pestanas.forEach(function (p, i) {
      var activa = i === indice;
      p.setAttribute("aria-selected", activa ? "true" : "false");
      p.tabIndex = activa ? 0 : -1;
      var panel = document.getElementById(p.getAttribute("aria-controls"));
      if (panel) { panel.hidden = !activa; }
    });
    if (enfocar) { pestanas[indice].focus(); }
  }

  pestanas.forEach(function (p, i) {
    p.addEventListener("click", function () { elegirPestana(i, false); });
    p.addEventListener("keydown", function (e) {
      var n = pestanas.length;
      var destino = null;
      if (e.key === "ArrowRight") { destino = (i + 1) % n; }
      else if (e.key === "ArrowLeft") { destino = (i - 1 + n) % n; }
      else if (e.key === "Home") { destino = 0; }
      else if (e.key === "End") { destino = n - 1; }
      if (destino !== null) {
        e.preventDefault();
        elegirPestana(destino, true);
      }
    });
  });

  /* ---------- Guía por uso (valores orientativos) ---------- */
  var USOS = {
    estudio: {
      titulo: "Estudio",
      procesador: "4 núcleos o más", ram: "8 GB", almacenamiento: "256 GB SSD", graficos: "Integrados",
      prioridad: "Batería y peso",
      nota: "Una portátil ligera con buena batería suele ser lo más práctico para estudiar."
    },
    oficina: {
      titulo: "Oficina",
      procesador: "4 núcleos o más", ram: "8 GB", almacenamiento: "256 GB SSD", graficos: "Integrados",
      prioridad: "Pantalla y teclado cómodos",
      nota: "Importa más un buen teclado y pantalla cómoda que la potencia: un todo en uno o una mini PC bastan."
    },
    diseno: {
      titulo: "Diseño",
      procesador: "6 núcleos o más", ram: "16 GB", almacenamiento: "512 GB SSD", graficos: "Dedicados o integrados potentes",
      prioridad: "Pantalla con buen color",
      nota: "Prioriza una pantalla con buena fidelidad de color y memoria suficiente para archivos grandes."
    },
    juegos: {
      titulo: "Juegos",
      procesador: "6 núcleos o más", ram: "16 GB", almacenamiento: "1 TB SSD", graficos: "Tarjeta gráfica dedicada",
      prioridad: "Tarjeta gráfica",
      nota: "La tarjeta gráfica pesa más que ninguna otra pieza; una de escritorio rinde más por el mismo precio."
    },
    programacion: {
      titulo: "Programación",
      procesador: "6 núcleos o más", ram: "16 GB", almacenamiento: "512 GB SSD", graficos: "Integrados",
      prioridad: "Memoria y SSD rápido",
      nota: "Mucha memoria y un SSD rápido aceleran compilar y abrir varios programas a la vez."
    }
  };

  var botonesUso = Array.prototype.slice.call(document.querySelectorAll("#guia button.uso"));
  var resultado = document.getElementById("guia-resultado");

  function mostrarUso(clave) {
    var datos = USOS[clave];
    if (!datos || !resultado) { return; }
    botonesUso.forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-uso") === clave ? "true" : "false");
    });
    document.getElementById("guia-uso-titulo").textContent = datos.titulo;
    var celdas = resultado.querySelectorAll("dd");
    var valores = [datos.procesador, datos.ram, datos.almacenamiento, datos.graficos, datos.prioridad];
    celdas.forEach(function (dd, i) { dd.textContent = valores[i]; });
    document.getElementById("guia-nota").textContent = datos.nota + " (Valores orientativos.)";
  }

  botonesUso.forEach(function (b) {
    b.addEventListener("click", function () { mostrarUso(b.getAttribute("data-uso")); });
  });

  /* ---------- Galería con ventana modal ---------- */
  var visor = document.getElementById("visor");
  var miniaturaActiva = null;

  if (visor && typeof visor.showModal === "function") {
    var imagenVisor = visor.querySelector("img");
    var leyendaVisor = document.getElementById("visor-leyenda");

    document.querySelectorAll("#galeria button.miniatura").forEach(function (m) {
      m.addEventListener("click", function () {
        var origen = m.querySelector("img");
        imagenVisor.setAttribute("src", origen.getAttribute("src"));
        imagenVisor.setAttribute("alt", origen.getAttribute("alt"));
        leyendaVisor.textContent = m.getAttribute("data-leyenda") || "";
        miniaturaActiva = m;
        visor.showModal();
      });
    });

    visor.querySelector(".cerrar").addEventListener("click", function () { visor.close(); });

    visor.addEventListener("click", function (e) {
      if (e.target === visor) { visor.close(); }
    });

    visor.addEventListener("close", function () {
      if (miniaturaActiva) { miniaturaActiva.focus(); }
    });
  }

  /* ---------- Formulario de contacto (demostración: no envía ni guarda nada) ---------- */
  var formulario = document.getElementById("formulario");

  if (formulario) {
    var campos = ["nombre", "correo", "tema", "mensaje"];
    var estado = document.getElementById("estado");
    var contador = document.getElementById("contador");
    var CORREO = /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/;

    var actualizarContador = function () {
      var n = document.getElementById("mensaje").value.length;
      contador.textContent = n + " de 500 caracteres";
    };

    var validar = function (campo, valor) {
      var limpio = valor.trim();
      if (campo === "nombre") {
        if (!limpio) { return "Escribe tu nombre."; }
        if (limpio.length > 80) { return "El nombre no puede pasar de 80 caracteres."; }
      } else if (campo === "correo") {
        if (!limpio) { return "Escribe tu correo electrónico."; }
        if (!CORREO.test(limpio)) { return "Escribe un correo válido, por ejemplo nombre@ejemplo.com."; }
      } else if (campo === "tema") {
        if (!limpio) { return "Elige un tema."; }
      } else if (campo === "mensaje") {
        if (!limpio) { return "Escribe tu mensaje."; }
        if (limpio.length < 10) { return "El mensaje debe tener al menos 10 caracteres."; }
        if (valor.length > 500) { return "El mensaje no puede pasar de 500 caracteres."; }
      }
      return "";
    };

    document.getElementById("mensaje").addEventListener("input", actualizarContador);

    formulario.addEventListener("submit", function (e) {
      e.preventDefault();
      estado.textContent = "";
      estado.classList.remove("exito");
      var primerError = null;

      campos.forEach(function (campo) {
        var entrada = document.getElementById(campo);
        var mensaje = validar(campo, entrada.value);
        document.getElementById("error-" + campo).textContent = mensaje;
        if (mensaje) {
          entrada.setAttribute("aria-invalid", "true");
          if (!primerError) { primerError = entrada; }
        } else {
          entrada.removeAttribute("aria-invalid");
        }
      });

      if (primerError) {
        primerError.focus();
        return;
      }

      var nombre = document.getElementById("nombre").value.trim();
      estado.classList.add("exito");
      estado.textContent = "Gracias, " + nombre + ". Esto es una demostración: tu mensaje no se envió ni se guardó en ningún lugar.";
      formulario.reset();
      actualizarContador();
    });
  }
})();
