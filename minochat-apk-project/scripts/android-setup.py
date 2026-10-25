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

# 4) плагины тянут новейшие androidx-библиотеки, которым нужен compileSdk 35, а наш Gradle собирает на 34.
#    Фиксируем версии, совместимые с 34.
gp = 'android/build.gradle'
g = open(gp, encoding='utf8').read()
if 'MinoChatPins' not in g:
    g += """

// MinoChatPins
allprojects {
    configurations.all {
        resolutionStrategy {
            force 'androidx.work:work-runtime:2.9.1'
            force 'androidx.work:work-runtime-ktx:2.9.1'
            force 'androidx.core:core:1.13.1'
            force 'androidx.core:core-ktx:1.13.1'
            force 'androidx.activity:activity:1.9.3'
            force 'androidx.lifecycle:lifecycle-runtime:2.8.7'
            force 'androidx.navigation:navigation-common:2.8.5'
            force 'androidx.navigation:navigation-runtime:2.8.5'
        }
    }
}
"""
    open(gp, 'w', encoding='utf8').write(g)
print('pins added')
