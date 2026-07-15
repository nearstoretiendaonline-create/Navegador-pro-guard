[app]
title = Chrome-Lite Anonymous
package.name = chromeliteanonymous
package.domain = com.chromelite.anonymous
source.dir = .
source.include_exts = py,txt
version = 0.1.0

requirements = python3,kivy==2.3.0,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = False
# Compila el WebViewClient real en Java (bloqueo de anuncios de verdad,
# no simulado) junto con el resto del APK.
android.add_src = src

[buildozer]
log_level = 2
warn_on_root = 1
