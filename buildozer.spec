[app]

title = XenonStandoff

package.name = xenonstandoff
package.domain = com.xenon

source.dir = .

source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy,requests

orientation = portrait

fullscreen = 0

android.permissions = INTERNET,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE

android.api = 34
android.minapi = 24

[buildozer]

log_level = 2
warn_on_root = 1
