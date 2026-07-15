"""
Chrome-Lite Anonymous — versión Kivy/Python para Pydroid 3.

Escribe y revisa este archivo en Pydroid 3 (sintaxis, lógica). El WebView
real de Android solo se activa en el APK compilado por GitHub Actions —
en Pydroid 3 corre en "modo simulado" (fallback de escritorio con
webbrowser) porque Pydroid no expone la vista nativa de Android a scripts
sueltos.

Arquitectura:
- Kivy dibuja la barra superior (omnibox + botones) en cualquier plataforma.
- En Android, se agrega un android.webkit.WebView real como vista nativa
  superpuesta al canvas de Kivy (técnica estándar: activity.addContentView).
- El bloqueador de anuncios/rastreadores y el forzado HTTPS corren en una
  clase Java real (src/org/chromelite/anonymous/PrivacyWebViewClient.java)
  que extiende WebViewClient y se compila junto al APK. Python solo la
  instancia, le pasa la lista de dominios bloqueados, y consulta su estado
  (contador de bloqueados, si está cargando) con un polling ligero.
"""

import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.utils import platform

BLOCKLIST_PATH = os.path.join(os.path.dirname(__file__), "blocklist.txt")


def load_blocklist():
    domains = set()
    if os.path.exists(BLOCKLIST_PATH):
        with open(BLOCKLIST_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    domains.add(line.lower())
    return domains


def normalize_input(text):
    text = text.strip()
    if text.startswith("http://") or text.startswith("https://"):
        return text
    if "." in text and " " not in text:
        return "https://" + text
    from urllib.parse import quote
    return "https://duckduckgo.com/?q=" + quote(text)


class ChromeLiteRoot(BoxLayout):
    """Barra superior de Kivy: omnibox + navegación + estado."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.blocked_count = 0
        self.blocklist = load_blocklist()

        toolbar = BoxLayout(size_hint_y=None, height=50, padding=4, spacing=4)
        self.btn_back = Button(text="<", size_hint_x=None, width=44)
        self.btn_back.bind(on_release=lambda *_: self.go_back())
        self.omnibox = TextInput(
            hint_text="Buscar o escribir una URL",
            multiline=False,
            size_hint_x=1,
        )
        self.omnibox.bind(on_text_validate=lambda *_: self.navigate())
        self.btn_go = Button(text="Ir", size_hint_x=None, width=50)
        self.btn_go.bind(on_release=lambda *_: self.navigate())
        self.btn_blocker = Button(text="Bloq: ON", size_hint_x=None, width=90)
        self.btn_blocker.bind(on_release=lambda *_: self.on_toggle_blocker())

        toolbar.add_widget(self.btn_back)
        toolbar.add_widget(self.omnibox)
        toolbar.add_widget(self.btn_go)
        toolbar.add_widget(self.btn_blocker)

        self.progress = ProgressBar(max=100, size_hint_y=None, height=4)
        self.status = Label(
            text="Listo. 0 rastreadores bloqueados.",
            size_hint_y=None,
            height=24,
        )

        self.add_widget(toolbar)
        self.add_widget(self.progress)
        self.add_widget(self.status)

        # El contenedor de abajo queda vacío en Kivy: en Android, el
        # WebView nativo se dibuja ENCIMA de esta ventana (ver
        # attach_android_webview). En escritorio, mostramos un aviso.
        if platform != "android":
            placeholder = Label(
                text=(
                    "[Vista previa de escritorio]\n"
                    "El WebView real solo funciona en el APK compilado "
                    "para Android.\nUsa este modo solo para revisar la "
                    "lógica de bloqueo y normalización de URLs."
                ),
                halign="center",
            )
            self.add_widget(placeholder)

        self.webview = None
        self.webview_client = None
        if platform == "android":
            self.attach_android_webview()

    def attach_android_webview(self):
        """Crea un android.webkit.WebView real y lo agrega a la Activity."""
        from jnius import autoclass

        WebView = autoclass("android.webkit.WebView")
        WebSettings = autoclass("android.webkit.WebSettings")
        CookieManager = autoclass("android.webkit.CookieManager")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        LayoutParams = autoclass("android.view.ViewGroup$LayoutParams")
        # Clase Java real compilada junto al APK (ver src/org/chromelite/anonymous/
        # PrivacyWebViewClient.java) — el filtrado de cada petición corre ahí,
        # no en Python, así que es rápido y no cruza el puente pyjnius por
        # cada recurso de la página.
        PrivacyWebViewClient = autoclass("org.chromelite.anonymous.PrivacyWebViewClient")

        activity = PythonActivity.mActivity
        webview = WebView(activity)
        settings = webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(False)
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE)
        settings.setUserAgentString(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )

        CookieManager.getInstance().setAcceptCookie(False)

        client = PrivacyWebViewClient()
        for domain in self.blocklist:
            client.addBlockedDomain(domain)
        webview.setWebViewClient(client)
        self.webview_client = client

        activity.addContentView(
            webview,
            LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT),
        )
        self.webview = webview

        # El WebViewClient vive en Java y no llama de vuelta a Python en
        # cada evento, así que consultamos su estado con un polling ligero
        # (2 veces por segundo es más que suficiente para una barra de
        # progreso y un contador).
        from kivy.clock import Clock
        Clock.schedule_interval(self._poll_webview_state, 0.5)

        self.navigate_to("https://duckduckgo.com")

    def _poll_webview_state(self, dt):
        if self.webview_client is None:
            return
        self.blocked_count = self.webview_client.getBlockedCount()
        loading = self.webview_client.isLoading()
        self.progress.value = 50 if loading else 100
        estado = "Cargando…" if loading else "Listo"
        self.status.text = f"{estado}. {self.blocked_count} rastreadores bloqueados."

    def toggle_blocker(self):
        if self.webview_client is not None:
            self.webview_client.setEnabled(not self.webview_client.isEnabled())

    def on_toggle_blocker(self):
        self.toggle_blocker()
        if self.webview_client is not None:
            is_on = self.webview_client.isEnabled()
            self.btn_blocker.text = "Bloq: ON" if is_on else "Bloq: OFF"
        else:
            self.status.text = "(Modo escritorio) El bloqueador solo aplica en Android."

    def navigate(self):
        self.navigate_to(normalize_input(self.omnibox.text))

    def navigate_to(self, url):
        self.omnibox.text = url
        if self.webview is not None:
            self.webview.loadUrl(url)
        else:
            self.status.text = f"(Modo escritorio) Navegaría a: {url}"

    def go_back(self):
        if self.webview is not None and self.webview.canGoBack():
            self.webview.goBack()


class ChromeLiteApp(App):
    title = "Chrome-Lite Anonymous"

    def build(self):
        return ChromeLiteRoot()

    def on_stop(self):
        """Purga cookies y datos al cerrar — incógnito por defecto."""
        if platform == "android":
            from jnius import autoclass

            CookieManager = autoclass("android.webkit.CookieManager")
            CookieManager.getInstance().removeAllCookies(None)


if __name__ == "__main__":
    ChromeLiteApp().run()
