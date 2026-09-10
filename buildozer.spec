[app]

title = RexCode Tools
package.name = rexcodetools
package.domain = com.rexcode

source.dir = .
source.include_exts = py,kv

version = 1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.api = 30
android.minapi = 24
android.archs = arm64-v8a

android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

[buildozer]

log_level = 2
