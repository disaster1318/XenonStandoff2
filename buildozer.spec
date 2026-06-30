[app]
source.dir = ./
title = Xenon
package.name = xenoncheat
package.domain = org.xenon
version = 1.1
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 30
android.arch = arm64-v8a
android.permissions = INTERNET
android.release_artifact = apk

# Эти строки заставят Buildozer скачать нужные инструменты
android.gradle_dependencies =
android.add_src =

[buildozer]
log_level = 2
warn_on_root = 1
