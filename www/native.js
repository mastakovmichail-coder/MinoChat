/* Мост для Android-приложения: уведомления через системные (WebView их не умеет). В браузере ничего не делает. */
(function () {
  const C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  const LN = C.Plugins && C.Plugins.LocalNotifications;
  if (!LN) return;
  let perm = 'default', seq = 1;
  LN.checkPermissions().then((r) => { perm = r.display === 'granted' ? 'granted' : r.display === 'denied' ? 'denied' : 'default'; }).catch(() => {});
  function N(title, opts) {
    opts = opts || {};
    LN.schedule({ notifications: [{ id: (seq++) % 2147483000, title: String(title), body: String(opts.body || ''), extra: { chatId: (opts.data && opts.data.chatId) || null }, smallIcon: 'ic_stat_icon', schedule: { at: new Date(Date.now() + 200) } }] }).catch(() => {});
    this.close = () => {};
  }
  Object.defineProperty(N, 'permission', { get: () => perm });
  N.requestPermission = async () => { try { const r = await LN.requestPermissions(); perm = r.display === 'granted' ? 'granted' : 'denied'; } catch { perm = 'denied'; } return perm; };
  window.Notification = N;
  try { LN.addListener('localNotificationActionPerformed', (e) => { const id = e && e.notification && e.notification.extra && e.notification.extra.chatId; if (id && typeof openChat === 'function') { try { openChat(id); } catch { /* ignore */ } } }); } catch { /* ignore */ }
  // системная кнопка "назад": закрыть окно/чат, на главном экране - свернуть
  try {
    const A = C.Plugins.App;
    if (A) A.addListener('backButton', () => {
      const m = document.querySelectorAll('.modal'); if (m.length) return m[m.length - 1].remove();
      if (typeof S !== 'undefined' && S.active && typeof closeChat === 'function') return closeChat();
      A.minimizeApp && A.minimizeApp();
    });
  } catch { /* ignore */ }
})();

/* ---------- автообновление интерфейса (без переустановки APK) ---------- */
(function () {
  const C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  const CU = C.Plugins && C.Plugins.CapacitorUpdater;
  if (!CU) return;
  const BASE = 'https://speeky-a0653.web.app';
  const num = (v) => String(v).split('.').reduce((a, x) => a * 1000 + (parseInt(x, 10) || 0), 0);
  const cur = () => { const m = document.querySelector('meta[name=ui-version]'); return m ? m.content : '0.0.0'; };
  let busy = false;
  const say = (t) => { try { if (typeof toast === 'function') toast(t); } catch { /* ignore */ } };
  async function apply(j) {
    if (busy) return; busy = true;
    try {
      say('Скачиваю обновление ' + j.version + '…');
      const b = await CU.download({ url: BASE + '/' + j.zip.replace(/^\//, ''), version: j.version });
      say('Обновление готово, перезапускаю…');
      setTimeout(() => CU.set(b), 1200);
    } catch (e) { busy = false; say('Не удалось обновить интерфейс'); }
  }
  window.__nativeUpdate = apply;
  async function check() {
    try {
      const r = await fetch(BASE + '/update/version.json?t=' + Date.now(), { cache: 'no-store' }); if (!r.ok) return;
      const j = await r.json(); if (num(j.version) > num(cur())) apply(j);
    } catch { /* нет сети */ }
  }
  // сообщаем плагину, что новая версия запустилась нормально (иначе он откатит обновление)
  try { CU.notifyAppReady(); } catch { /* ignore */ }
  setTimeout(check, 4000);
  try { const A = C.Plugins.App; if (A) A.addListener('appStateChange', (s) => { if (s && s.isActive) setTimeout(check, 1500); }); } catch { /* ignore */ }
  setInterval(check, 30 * 60 * 1000);
})();
