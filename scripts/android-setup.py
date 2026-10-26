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

# 8) плагин Google-входа не подтягивает play-services-auth сам (без неё приложение падает при запуске)
ap2 = 'android/app/build.gradle'
a2 = open(ap2, encoding='utf8').read()
if 'MinoChatDeps' not in a2:
    a2 += """

// MinoChatDeps
dependencies {
    implementation 'com.google.android.gms:play-services-auth:21.2.0'
}
"""
    open(ap2, 'w', encoding='utf8').write(a2)
print('play-services-auth added')

# 9) уведомления при закрытом приложении: служба переднего плана держит MinoChat живым в фоне
import glob as _glob
_jd = os.path.dirname(_glob.glob('android/app/src/main/java/**/MainActivity.java', recursive=True)[0])
_pk = 'app.minochat.mobile'
open(_jd + '/KeepAliveService.java', 'w', encoding='utf8').write('''package %s;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;

public class KeepAliveService extends Service {
    static final String CH = "minochat_keepalive";

    @Override public IBinder onBind(Intent i) { return null; }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && "STOP".equals(intent.getAction())) {
            SharedPreferences p = getSharedPreferences("mc", Context.MODE_PRIVATE);
            p.edit().putBoolean("keepalive_off", true).apply();
            stopForeground(true);
            stopSelf();
            return START_NOT_STICKY;
        }
        NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel c = new NotificationChannel(CH, "Работа в фоне", NotificationManager.IMPORTANCE_MIN);
            c.setShowBadge(false);
            nm.createNotificationChannel(c);
        }
        Intent open = new Intent(this, MainActivity.class);
        open.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        int fl = PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= 23 ? PendingIntent.FLAG_IMMUTABLE : 0);
        PendingIntent pi = PendingIntent.getActivity(this, 0, open, fl);
        Intent stop = new Intent(this, KeepAliveService.class); stop.setAction("STOP");
        PendingIntent ps = PendingIntent.getService(this, 1, stop, fl);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, CH) : new Notification.Builder(this);
        b.setSmallIcon(getResources().getIdentifier("ic_stat_icon", "drawable", getPackageName()))
         .setContentTitle("MinoChat")
         .setContentText("Работает в фоне, чтобы приходили сообщения")
         .setContentIntent(pi)
         .setOngoing(true)
         .addAction(new Notification.Action.Builder(null, "Выключить", ps).build());
        Notification n = b.build();
        if (Build.VERSION.SDK_INT >= 34) startForeground(7, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        else startForeground(7, n);
        return START_STICKY;
    }
}
''' % _pk)
open(_jd + '/MainActivity.java', 'w', encoding='utf8').write('''package %s;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Settings;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        SharedPreferences p = getSharedPreferences("mc", Context.MODE_PRIVATE);
        p.edit().putBoolean("keepalive_off", false).apply();
        try {
            Intent i = new Intent(this, KeepAliveService.class);
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(i); else startService(i);
        } catch (Exception e) { /* ignore */ }
        // один раз просим не засыпать в фоне (иначе Android может остановить связь с сервером)
        new Handler(Looper.getMainLooper()).postDelayed(new Runnable() { public void run() {
            try {
                SharedPreferences q = getSharedPreferences("mc", Context.MODE_PRIVATE);
                PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
                if (Build.VERSION.SDK_INT >= 23 && !q.getBoolean("battery_asked", false) && !pm.isIgnoringBatteryOptimizations(getPackageName())) {
                    q.edit().putBoolean("battery_asked", true).apply();
                    Intent r = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:" + getPackageName()));
                    startActivity(r);
                }
            } catch (Exception e) { /* ignore */ }
        } }, 6000);
    }

    // WebView не должен «засыпать», когда приложение свернуто, иначе сообщения перестанут приходить
    @Override public void onStop() {
        super.onStop();
        try { getBridge().getWebView().onResume(); getBridge().getWebView().resumeTimers(); } catch (Exception e) { /* ignore */ }
    }
}
''' % _pk)
_m = open(MAN, encoding='utf8').read()
_perm = ''.join('    <uses-permission android:name="android.permission.%s" />\n' % p for p in ['FOREGROUND_SERVICE', 'FOREGROUND_SERVICE_SPECIAL_USE', 'WAKE_LOCK', 'REQUEST_IGNORE_BATTERY_OPTIMIZATIONS'] if p not in _m)
_m = _m.replace('</manifest>', _perm + '</manifest>')
if 'KeepAliveService' not in _m:
    _m = _m.replace('</application>', '''        <service android:name=".KeepAliveService" android:exported="false" android:foregroundServiceType="specialUse">
            <property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE" android:value="messaging" />
        </service>
    </application>''')
open(MAN, 'w', encoding='utf8').write(_m)
print('keep-alive service added')

# 10) автообновление самого APK: мост MCNative (версия, разрешение, скачивание, установка)
_jd2 = os.path.dirname(_glob.glob('android/app/src/main/java/**/MainActivity.java', recursive=True)[0])
open(_jd2 + '/McFileProvider.java', 'w', encoding='utf8').write('package app.minochat.mobile;\n\npublic class McFileProvider extends androidx.core.content.FileProvider {}\n')
open(_jd2 + '/MCNative.java', 'w', encoding='utf8').write('''package app.minochat.mobile;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import android.webkit.JavascriptInterface;
import androidx.core.content.FileProvider;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class MCNative {
    private final Activity act;
    MCNative(Activity a) { act = a; }

    @JavascriptInterface public int versionCode() {
        try {
            PackageInfo p = act.getPackageManager().getPackageInfo(act.getPackageName(), 0);
            return (int) (Build.VERSION.SDK_INT >= 28 ? p.getLongVersionCode() : p.versionCode);
        } catch (Exception e) { return 0; }
    }

    @JavascriptInterface public boolean canInstall() {
        return Build.VERSION.SDK_INT < 26 || act.getPackageManager().canRequestPackageInstalls();
    }

    @JavascriptInterface public void allowInstall() {
        act.runOnUiThread(new Runnable() { public void run() {
            try { act.startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + act.getPackageName()))); } catch (Exception e) { /* ignore */ }
        } });
    }

    private void state(final String s) {
        act.runOnUiThread(new Runnable() { public void run() {
            try { ((MainActivity) act).getBridge().getWebView().evaluateJavascript("window.__apkState&&window.__apkState('" + s + "')", null); } catch (Exception e) { /* ignore */ }
        } });
    }

    @JavascriptInterface public void install(final String url) {
        if (url == null || !url.startsWith("https://speeky-a0653.web.app/")) { state("error"); return; }
        new Thread(new Runnable() { public void run() {
            try {
                File dir = new File(act.getCacheDir(), "updates"); dir.mkdirs();
                File f = new File(dir, "MinoChat.apk"); if (f.exists()) f.delete();
                HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
                c.setConnectTimeout(20000); c.setReadTimeout(60000);
                if (c.getResponseCode() != 200) { state("error"); return; }
                InputStream in = c.getInputStream(); FileOutputStream out = new FileOutputStream(f);
                byte[] buf = new byte[65536]; int n; long total = 0;
                while ((n = in.read(buf)) > 0) { out.write(buf, 0, n); total += n; }
                out.close(); in.close();
                if (total < 100000) { state("error"); return; }
                Uri u = FileProvider.getUriForFile(act, act.getPackageName() + ".mcupdate", f);
                Intent i = new Intent(Intent.ACTION_VIEW);
                i.setDataAndType(u, "application/vnd.android.package-archive");
                i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
                state("ready");
                act.startActivity(i);
            } catch (Exception e) { state("error"); }
        } }).start();
    }
}
''')
os.makedirs(RES + '/xml', exist_ok=True)
open(RES + '/xml/mc_paths.xml', 'w', encoding='utf8').write('<?xml version="1.0" encoding="utf-8"?>\n<paths>\n    <cache-path name="mcupdates" path="updates/" />\n</paths>\n')
_m2 = open(MAN, encoding='utf8').read()
if 'REQUEST_INSTALL_PACKAGES' not in _m2:
    _m2 = _m2.replace('</manifest>', '    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />\n</manifest>')
if 'McFileProvider' not in _m2:
    _m2 = _m2.replace('</application>', '''        <provider android:name=".McFileProvider" android:authorities="${applicationId}.mcupdate" android:exported="false" android:grantUriPermissions="true">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/mc_paths" />
        </provider>
    </application>''')
open(MAN, 'w', encoding='utf8').write(_m2)
_ma = open(_jd2 + '/MainActivity.java', encoding='utf8').read()
if 'MCNative' not in _ma:
    _ma = _ma.replace('        super.onCreate(b);\n', '        super.onCreate(b);\n        try { getBridge().getWebView().addJavascriptInterface(new MCNative(this), "MCNative"); } catch (Exception e) { /* ignore */ }\n', 1)
    open(_jd2 + '/MainActivity.java', 'w', encoding='utf8').write(_ma)
# versionCode / versionName из package.json (3.7.0 -> 30700), чтобы приложение понимало, что вышла новая версия
import json as _json
_ver = _json.load(open('package.json'))['version']; _p = [int(x) for x in _ver.split('.')]
_code = _p[0] * 10000 + _p[1] * 100 + _p[2]
_ag = open('android/app/build.gradle', encoding='utf8').read()
_ag = _re.sub(r'versionCode\s+\d+', 'versionCode %d' % _code, _ag, count=1)
_ag = _re.sub(r'versionName\s+"[^"]*"', 'versionName "%s"' % _ver, _ag, count=1)
open('android/app/build.gradle', 'w', encoding='utf8').write(_ag)
open('apk.json', 'w', encoding='utf8').write(_json.dumps({'versionCode': _code, 'versionName': _ver, 'file': 'MinoChat.apk'}))
print('apk self-update bridge added, versionCode', _code)
