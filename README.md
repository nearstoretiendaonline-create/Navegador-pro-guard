# Chrome-Lite Anonymous (versión Python/Kivy para Pydroid 3)

Esta es una variante del navegador escrita en **Python + Kivy** en vez de
Kotlin, pensada para que puedas editar el código directamente en **Pydroid 3**
desde el celular. La compilación a `.apk` ocurre **100% en GitHub Actions**
usando `buildozer` — no necesitas Android Studio, SDK ni NDK en tu teléfono.

## ⚠️ Limitación importante (léelo antes de empezar)

Pydroid 3 te deja **escribir y revisar errores de sintaxis** en `main.py`,
pero **no puedes ver el navegador funcionando dentro de Pydroid**. El
`WebView` real de Android solo se activa dentro del `.apk` ya compilado e
instalado — Pydroid corre tu script en su propio proceso y no te deja
insertar una vista nativa ahí. Trata Pydroid como tu editor de texto con
detección de errores, no como una vista previa en vivo.

También, a diferencia de la versión Kotlin, el **bloqueo de anuncios a
nivel de red ya está implementado de verdad** — no en Python, sino en una
pequeña clase Java (`src/org/chromelite/anonymous/PrivacyWebViewClient.java`)
que se compila junto con el resto del APK. Filtra cada petición antes de
que salga del dispositivo, igual que la versión Kotlin, y Python solo la
alimenta con la lista de dominios y consulta el contador de bloqueados.

## Qué incluye

| Archivo | Qué hace |
|---|---|
| `main.py` | App Kivy: omnibox, botón atrás, botón de bloqueador, WebView nativo vía `pyjnius` |
| `src/org/chromelite/anonymous/PrivacyWebViewClient.java` | Bloqueo real de anuncios/rastreadores + forzado HTTPS, compilado junto al APK |
| `blocklist.txt` | Lista de dominios de anuncios/rastreo (misma que la versión Kotlin) |
| `buildozer.spec` | Configuración de compilación: permisos, versión de Android, `android.add_src` para incluir el Java |
| `.github/workflows/build.yml` | Compila el APK en GitHub Actions con `buildozer` |

## Cómo compilar (todo en GitHub, sin nada local)

1. Sube esta carpeta (`pydroid-chrome-lite`) como repositorio nuevo en
   GitHub — misma idea que antes: "Add file" → "Upload files" → botón
   **"choose your files"** → selecciona todo el contenido de la carpeta.
   Asegúrate de que la carpeta `.github` sí se suba.
2. Ve a la pestaña **Actions** de tu repo. El workflow **"Build Debug APK
   (Buildozer)"** arranca solo con el push, o lo lanzas a mano con **Run
   workflow**.
3. **La primera compilación tarda entre 25 y 40 minutos** — descarga y
   arma todo el NDK de Android desde cero. Las siguientes son más rápidas
   por el caché. No necesitas quedarte mirando, GitHub sigue corriendo en
   la nube aunque cierres la app.
4. Cuando el run se ponga verde ✅, entra a él → sección **Artifacts** →
   descarga `chrome-lite-anonymous-debug` → adentro está el `.apk`.
5. Instálalo en tu teléfono igual que antes: ábrelo desde el explorador de
   archivos y confirma "instalar de fuentes desconocidas".

## Editar el código desde Pydroid 3

1. Copia `main.py`, `blocklist.txt` y `buildozer.spec` a una carpeta en tu
   teléfono (por ejemplo dentro de `Descargas/pydroid-chrome-lite/`).
2. Abre Pydroid 3 → icono de carpeta → navega hasta `main.py` y ábrelo ahí.
3. Pydroid te subraya errores de sintaxis mientras escribes. Puedes
   ejecutar el archivo dentro de Pydroid para revisar la lógica de
   `normalize_input()` y `load_blocklist()` — esas partes sí corren en
   modo escritorio/simulado.
4. Cuando termines de editar, vuelve a subir el archivo modificado a
   GitHub (reemplazando el anterior desde "Add file" → "Upload files") y
   deja que Actions lo recompile.

## Ampliar la lista de bloqueo

`blocklist.txt` trae ~50 dominios conocidos como punto de partida. Para
cobertura más completa, fusiónala con una lista pública activa, por
ejemplo StevenBlack (github.com/StevenBlack/hosts) o EasyList — basta con
añadir más líneas de dominio (uno por línea, sin `http://`) a ese mismo
archivo; `main.py` y la clase Java las cargan automáticamente al iniciar.
