# Núcleo · PWA en cuatro modos de visualización

La página original (raíz: `index.html`, `css/`, `js/`, `img/`…) **no se modificó**. Cada carpeta
es una copia completa de la página convertida en PWA, con su propio manifest, service worker,
caché e iconos. El contenido y el diseño son los mismos; solo cambian `display` y `orientation`.

| Integrante | Carpeta | `display` | `orientation` | URL (GitHub Pages) |
|---|---|---|---|---|
| 1 | `browser/` | browser | any | https://gimi34.github.io/act2pwa/browser/ |
| 2 | `minimal-ui/` | minimal-ui | portrait | https://gimi34.github.io/act2pwa/minimal-ui/ |
| 3 | `standalone/` | standalone | portrait | https://gimi34.github.io/act2pwa/standalone/ |
| 4 | `fullscreen/` | fullscreen | landscape | https://gimi34.github.io/act2pwa/fullscreen/ |

## Qué contiene cada versión

- `manifest.json`: `name`, `short_name`, `id`, `start_url`, `scope`, `display`, `orientation`,
  `theme_color`, `background_color` e iconos (192, 512 y maskable).
- `sw.js`: service worker. Al instalarse guarda todos los archivos en **Cache Storage**
  (`nucleo-<carpeta>-v5`); después responde primero desde la caché (cache first),
  salvo `manifest.json`, que se pide primero a la red para que los cambios lleguen. Por eso
  la app abre **sin conexión**. Al activarse borra cachés viejas de su versión.
- `js/pwa.js`: registra el service worker, muestra el botón flotante «Instalar app» (abre la ventana
  de instalación del navegador; si el navegador no la ofrece, explica cómo instalar desde su menú) y un aviso abajo cuando no hay internet;
  al volver la conexión dice «Conexión restablecida» y desaparece a los 3 segundos.
- `index.html`: el original + `<link rel="manifest">`, `theme-color`, metas para iOS y el aviso de conexión.

## Publicar en GitHub Pages

1. Sube los cambios: `git add . && git commit -m "PWA en 4 modos" && git push`.
2. En GitHub: **Settings → Pages → Source: Deploy from a branch → main / (root) → Save**.
3. En 1–2 minutos quedan las cuatro URLs de la tabla (GitHub Pages da HTTPS, obligatorio para PWA).

## Cambiar una orientación

Edita la tabla `VERSIONES` en `herramientas/generar_pwa.py`, sube `VERSION_CACHE` (v2, v3…)
y ejecuta `python herramientas/generar_pwa.py` desde esta carpeta. Si cambias la página
original, ejecuta lo mismo para copiar los cambios a las cuatro versiones.

## Qué esperar en la demostración (Android + Chrome)

Abre la URL en Chrome, instala (botón «Instalar app» o menú ⋮ → *Instalar app* /
*Agregar a pantalla principal*) y abre la app **desde el icono**.

- **browser + any**: se abre como pestaña normal de Chrome con barra de direcciones. El
  navegador ignora `orientation` en este modo; la página gira libremente si la rotación
  automática del teléfono está activada. Chrome puede no ofrecer «Instalar» (solo crea un
  acceso directo), porque `browser` no cumple el criterio de app instalable.
- **minimal-ui + portrait**: ventana propia con una barra mínima (URL / atrás / recargar).
  Se mantiene vertical aunque se gire el teléfono. Según el navegador la barra puede ser muy discreta o casi igual a standalone; si no soporta
  minimal-ui, la especificación indica caer a `browser`.
- **standalone + portrait**: ventana propia sin barra de direcciones, con barra de estado
  del sistema. Se mantiene vertical aunque se gire el teléfono.
- **fullscreen + landscape**: ocupa toda la pantalla, sin barra de estado ni navegación.
  Se abre en horizontal y se queda así.

Para mostrar la configuración, abre `manifest.json` (o Chrome DevTools → Application → Manifest).

**Variaciones normales**: iPhone/iPad (Safari) ignora `orientation` y solo soporta bien
`standalone` (los otros modos se ven como standalone o como Safari normal); algunas tabletas o el bloqueo de rotación del sistema pueden
impedir el giro. Si pasa, muestra `manifest.json` (o Chrome DevTools → Application → Manifest)
para demostrar que la configuración es correcta y explica la diferencia.

**Para probar sin conexión**: abre la app una vez con internet, activa el modo avión y vuelve
a abrirla; aparecerá el aviso «Sin conexión a internet» y la página cargará igual.
