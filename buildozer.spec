[app]
title = XenonStandoff
package.name = xenonstandoff
package.domain = com.xenon.standoff
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy,requests,opencv-python,numpy
orientation = portrait
fullscreen = 1
android.permissions = INTERNET, SYSTEM_ALERT_WINDOW, FOREGROUND_SERVICE
android.api = 30
android.minapi = 24
android.ndk = 28c
[buildozer]
log_level = 2
warn_on_root = 0
