# Запускается после "npx cap add android": права, иконки, название, цвета.
import os, re, shutil
from PIL import Image
RES = 'android/app/src/main/res'
MAN = 'android/app/src/main/AndroidManifest.xml'

# 1) права
m = open(MAN, encoding='utf8').read()
perms = ['INTERNET', 'RECORD_AUDIO', 'CAMERA', 'MODIFY_AUDIO_SETTINGS', 'POST_NOTIFICATIONS', 'VIBRATE', 'ACCESS_NETWORK_STATE']
add = ''.join('    <uses-permission android:name="android.permission.%s" />\n' % p for p in perms if p not in m)
add += '    <uses-feature android:name="android.hardware.camera" android:required="false" />\n    <uses-feature android:name="android.hardware.microphone" android:required="false" />\n'
m = m.replace('</manifest>', add + '</manifest>')
m = m.replace('android:label="@string/app_name"', 'android:label="MinoChat"', 1)
open(MAN, 'w', encoding='utf8').write(m)

# 2) иконки приложения (обычные квадратные, без адаптивных)
src = Image.open('icon.png').convert('RGBA')
sizes = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
shutil.rmtree(RES + '/mipmap-anydpi-v26', ignore_errors=True)
for d, px in sizes.items():
    dd = '%s/mipmap-%s' % (RES, d); os.makedirs(dd, exist_ok=True)
    for f in os.listdir(dd):
        if f.startswith('ic_launcher'): os.remove(os.path.join(dd, f))
    im = src.resize((px, px), Image.LANCZOS)
    im.save(dd + '/ic_launcher.png'); im.save(dd + '/ic_launcher_round.png'); im.save(dd + '/ic_launcher_foreground.png')
# значок уведомления (белый силуэт)
os.makedirs(RES + '/drawable', exist_ok=True)
st = src.resize((96, 96), Image.LANCZOS); a = st.split()[3]
w = Image.new('RGBA', (96, 96), (255, 255, 255, 0)); w.putalpha(a); w.save(RES + '/drawable/ic_stat_icon.png')

# 3) цвета и сплэш
cl = RES + '/values/colors.xml'
open(cl, 'w', encoding='utf8').write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="colorPrimary">#050814</color>\n    <color name="colorPrimaryDark">#050814</color>\n    <color name="colorAccent">#2F6BFF</color>\n</resources>\n')
sp = Image.new('RGB', (480, 480), (5, 8, 20)); sp.paste(src.resize((220, 220), Image.LANCZOS), (130, 130), src.resize((220, 220), Image.LANCZOS))
for d in os.listdir(RES):
    if d.startswith('drawable') and os.path.exists(RES + '/' + d + '/splash.png'): sp.save(RES + '/' + d + '/splash.png')
print('android setup done')

# 4) современный инструментарий (Android 15, AGP 8.7, Gradle 8.9): плагины рассчитаны на него,
#    поэтому никаких принудительных понижений версий библиотек не нужно (они ломали запуск приложения).
import re as _re0
bp = 'android/build.gradle'
b = open(bp, encoding='utf8').read()
b = _re0.sub(r"com\.android\.tools\.build:gradle:[\d.]+", "com.android.tools.build:gradle:8.7.2", b)
open(bp, 'w', encoding='utf8').write(b)
wp = 'android/gradle/wrapper/gradle-wrapper.properties'
w = open(wp, encoding='utf8').read()
w = _re0.sub(r"gradle-[\d.]+-(all|bin)\.zip", "gradle-8.9-all.zip", w)
open(wp, 'w', encoding='utf8').write(w)
vp0 = 'android/variables.gradle'
v0 = open(vp0, encoding='utf8').read()
v0 = _re0.sub(r"compileSdkVersion\s*=\s*\d+", "compileSdkVersion = 35", v0)
open(vp0, 'w', encoding='utf8').write(v0)
print('toolchain updated')

# 5) библиотеки Google требуют Android 6.0+ (minSdk 23)
import re as _re
vp = 'android/variables.gradle'
v = open(vp, encoding='utf8').read()
v = _re.sub(r'minSdkVersion\s*=\s*\d+', 'minSdkVersion = 23', v)
open(vp, 'w', encoding='utf8').write(v)
print('minSdk 23')

# 6) постоянный ключ подписи (чтобы SHA-1 не менялся между сборками - нужен для входа через Google)
ap = 'android/app/build.gradle'
a = open(ap, encoding='utf8').read()
if 'MinoChatSign' not in a:
    a += """

// MinoChatSign
android {
    signingConfigs {
        debug {
            storeFile file('../../minochat.keystore')
            storePassword 'minochat123'
            keyAlias 'minochat'
            keyPassword 'minochat123'
        }
    }
}
"""
    open(ap, 'w', encoding='utf8').write(a)
# 7) google-services.json (из Firebase Console) кладём куда нужно
import os as _os, shutil as _sh
if _os.path.exists('google-services.json'):
    _sh.copy('google-services.json', 'android/app/google-services.json'); print('google-services.json copied')
else:
    print('WARNING: google-services.json not found - Google sign-in will not work on Android')
