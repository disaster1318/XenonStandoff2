[app]
source.dir = ./
title = Xenon
package.name = xenoncheat
package.domain = org.xenon
version = 1.1
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# ========== ФИКС AIDL ==========
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 30
android.arch = arm64-v8a
android.permissions = INTERNET
android.release_artifact = apk

# Принудительная установка SDK
android.gradle_dependencies =
android.add_src =

# ========== ФИКС AIDL КОНЕЦ ==========

[buildozer]
log_level = 2
warn_on_root = 1
