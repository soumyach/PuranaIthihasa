// Temple tips helper (self-contained so it doesn't depend on community.js merge
// order). Reads approved tips publicly; submitting requires a signed-in user
// (RLS). New tips default to moderation_status='pending' (hold-until-approved);
// an admin flips them to 'approved' in the Supabase table editor.
(function () {
  let client = null;
  let ready = null;
  let currentUser = null;

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      const s = document.createElement('script');
      s.src = src; s.async = true; s.onload = resolve; s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function init() {
    if (ready) return ready;
    ready = (async function () {
      try {
        const r = await fetch('/api/public-config');
        if (!r.ok) return null;
        const cfg = await r.json();
        if (!cfg || !cfg.configured || !cfg.supabaseUrl || !cfg.supabaseAnonKey) return null;
        if (!(window.supabase && window.supabase.createClient)) {
          await loadScript('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js');
        }
        client = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey, {
          auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
        });
        const s = await client.auth.getSession();
        currentUser = (s && s.data && s.data.session) ? s.data.session.user : null;
        return client;
      } catch (e) { return null; }
    })();
    return ready;
  }

  async function listApproved(templeSlug) {
    const c = await init();
    if (!c) return null; // not configured
    try {
      const res = await c.from('user_tips')
        .select('tip_type,title,body,visit_month,created_at')
        .eq('temple_id', templeSlug)
        .eq('moderation_status', 'approved')
        .order('created_at', { ascending: false })
        .limit(30);
      return res.data || [];
    } catch (e) { return []; }
  }

  async function submit(templeSlug, tipType, body, visitMonth) {
    const c = await init();
    if (!c) return { ok: false, reason: 'config' };
    if (!currentUser) return { ok: false, reason: 'auth' };
    const text = String(body || '').trim().slice(0, 1000);
    if (!text) return { ok: false, reason: 'empty' };
    try {
      const res = await c.from('user_tips').insert({
        user_id: currentUser.id,
        temple_id: templeSlug,
        tip_type: tipType || 'general',
        body: text,
        visit_month: visitMonth || null
      });
      return { ok: !res.error, error: res.error && res.error.message };
    } catch (e) { return { ok: false, error: String(e) }; }
  }

  async function signedIn() { await init(); return !!currentUser; }

  window.KhatakshetraTips = { init: init, listApproved: listApproved, submit: submit, signedIn: signedIn };
})();
