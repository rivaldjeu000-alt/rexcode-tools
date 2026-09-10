[app]

title = RexCode Tools
package.name = rexcodetools
package.domain = com.rexcode

source.dir = .
source.include_exts = py,kv,png,jpg,json,ttf

version = 1.0

requirements = python3,kivy,lz4

orientation = portrait
fullscreen = 0

android.api = 28
android.minapi = 28
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

[buildozer]

log_level = 2
