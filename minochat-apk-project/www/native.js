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
