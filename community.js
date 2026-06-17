// Khatakshetra community helpers (shared). Talks to Supabase with the public
// anon key (RLS-protected). Graceful: every method no-ops/returns empty until
// the project is configured (/api/public-config). Auth session is shared with
// site.js via localStorage, so a user who signed in via the magic-link modal is
// recognised here too.
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

  function weekStart() {
    const d = new Date();
    const day = (d.getDay() + 6) % 7; // 0 = Monday
    d.setDate(d.getDate() - day);
    return d.toISOString().slice(0, 10);
  }
  function getProfile() {
    try { return (typeof getKhatakshetraProfile === 'function') ? getKhatakshetraProfile() : JSON.parse(localStorage.getItem('khatakshetra_profile') || '{}'); }
    catch (e) { return {}; }
  }
  function saveProfile(p) {
    if (typeof saveKhatakshetraProfile === 'function') saveKhatakshetraProfile(p);
    else localStorage.setItem('khatakshetra_profile', JSON.stringify(p));
  }

  async function refreshOwnEntry() {
    const c = await init();
    if (!c || !currentUser) return false;
    const p = getProfile();
    if (!p.leaderboard || !p.leaderboard.optIn) return false;
    try {
      await c.from('leaderboard_entries').upsert({
        user_id: currentUser.id,
        handle: (p.leaderboard.handle || p.child_name || 'A learner').slice(0, 40),
        xp: p.xp || 0,
        level: p.level || 1,
        week_start: weekStart(),
        updated_at: new Date().toISOString()
      }, { onConflict: 'user_id' });
      return true;
    } catch (e) { return false; }
  }

  async function join(handle) {
    const c = await init();
    if (!c) return { ok: false, reason: 'config' };
    if (!currentUser) return { ok: false, reason: 'auth' };
    const p = getProfile();
    p.leaderboard = { optIn: true, handle: (handle || p.child_name || 'A learner').slice(0, 40) };
    saveProfile(p);
    await refreshOwnEntry();
    return { ok: true };
  }

  async function leave() {
    const c = await init();
    const p = getProfile();
    p.leaderboard = { optIn: false, handle: (p.leaderboard && p.leaderboard.handle) || '' };
    saveProfile(p);
    if (c && currentUser) { try { await c.from('leaderboard_entries').delete().eq('user_id', currentUser.id); } catch (e) {} }
    return { ok: true };
  }

  async function top(limit) {
    const c = await init();
    if (!c) return null; // null = not configured (caller shows a friendly note)
    try {
      const res = await c.from('leaderboard_entries')
        .select('handle,xp,level')
        .eq('week_start', weekStart())
        .order('xp', { ascending: false })
        .limit(limit || 25);
      return res.data || [];
    } catch (e) { return []; }
  }

  async function status() {
    await init();
    const p = getProfile();
    return {
      configured: !!client,
      signedIn: !!currentUser,
      optedIn: !!(p.leaderboard && p.leaderboard.optIn),
      handle: (p.leaderboard && p.leaderboard.handle) || p.child_name || ''
    };
  }

  window.KhatakshetraCommunity = { init: init, join: join, leave: leave, top: top, status: status, refreshOwnEntry: refreshOwnEntry, weekStart: weekStart };
})();
