/**
 * /api/diag — safe, read-only deployment diagnostics.
 * Reports WHICH configuration is present and whether Supabase tables are
 * reachable, WITHOUT ever revealing secret values (booleans only).
 * Use it to answer "why isn't email/preferences working?" in one request.
 */
export default async function handler(req, res) {
  const out = {
    ok: true,
    runtime: { node: process.version },
    env: {
      SUPABASE_URL: !!process.env.SUPABASE_URL,
      SUPABASE_SERVICE_ROLE_KEY: !!(process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY),
      SUPABASE_ANON_KEY: !!process.env.SUPABASE_ANON_KEY,
      GMAIL_CLIENT_ID: !!process.env.GMAIL_CLIENT_ID,
      GMAIL_CLIENT_SECRET: !!process.env.GMAIL_CLIENT_SECRET,
      GMAIL_REFRESH_TOKEN: !!process.env.GMAIL_REFRESH_TOKEN,
      WELCOME_FROM: !!process.env.WELCOME_FROM
    },
    tables: {},
    welcomeEmailModule: null,
    welcomeEmailReady: false
  };

  // Can the welcome-email helper actually be imported in this bundle?
  try {
    const mod = await import('../lib/welcome-email.js');
    out.welcomeEmailModule = typeof mod.sendWelcomeEmail === 'function' ? 'ok' : 'loaded-but-missing-export';
  } catch (e) {
    out.welcomeEmailModule = 'import-failed: ' + String((e && e.message) || e);
  }
  out.welcomeEmailReady = out.welcomeEmailModule === 'ok' &&
    out.env.GMAIL_CLIENT_ID && out.env.GMAIL_CLIENT_SECRET && out.env.GMAIL_REFRESH_TOKEN;

  // Are the tables we depend on reachable? (HEAD-style probe, no rows returned.)
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;
  if (url && key) {
    const headers = { apikey: key, Authorization: 'Bearer ' + key };
    for (const t of ['email_captures', 'email_subscribers']) {
      try {
        const r = await fetch(`${url.replace(/\/$/, '')}/rest/v1/${t}?select=*&limit=0`, { headers });
        out.tables[t] = r.ok ? 'ok' : `error ${r.status}: ${(await r.text()).slice(0, 160)}`;
      } catch (e) {
        out.tables[t] = 'fetch-failed: ' + String((e && e.message) || e);
      }
    }
  }

  res.setHeader('Cache-Control', 'no-store');
  return res.status(200).json(out);
}
