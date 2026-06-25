[app]

title = XenonStandoff

package.name = xenonstandoff
package.domain = com.xenon

source.dir = .
source.include_exts = py,png,jpg,kv

version = 1.0

requirements = python3,kivy,requests

orientation = portrait

fullscreen = 0

android.api = 33
android.minapi = 24
android.ndk = 25b

android.permissions = INTERNET

[buildozer]

log_level = 2
warn_on_root = 1
