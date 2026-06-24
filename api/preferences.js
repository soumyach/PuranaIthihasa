/**
 * /api/preferences — read & update a subscriber's email preferences by token.
 *   GET  /api/preferences?token=UUID            -> { email, subscribed, weekly_digest }
 *   POST /api/preferences?token=UUID  (JSON)     -> { subscribed?, weekly_digest? } updates
 *   POST /api/preferences?token=UUID&unsubscribe=1  OR  RFC 8058 one-click body
 *        (List-Unsubscribe=One-Click)            -> sets subscribed = false
 * Uses the Supabase service role (server-side); the token is the only credential.
 */
export default async function handler(req, res) {
  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;
  if (!supabaseUrl || !serviceRoleKey) {
    return res.status(500).json({ error: 'Server is not configured' });
  }

  const token = String((req.query && (req.query.token || req.query.t)) || '').trim();
  if (!token) return res.status(400).json({ error: 'Missing token' });

  const base = `${supabaseUrl.replace(/\/$/, '')}/rest/v1/email_subscribers`;
  const H = { apikey: serviceRoleKey, Authorization: `Bearer ${serviceRoleKey}` };

  if (req.method === 'GET') {
    const r = await fetch(`${base}?token=eq.${encodeURIComponent(token)}&select=email,subscribed,weekly_digest`, { headers: H });
    if (!r.ok) return res.status(502).json({ error: 'Lookup failed' });
    const rows = await r.json();
    if (!Array.isArray(rows) || !rows.length) return res.status(404).json({ error: 'Not found' });
    return res.status(200).json(rows[0]);
  }

  if (req.method === 'POST') {
    const rawBody = typeof req.body === 'string' ? req.body : '';
    const oneClick = (rawBody && rawBody.indexOf('List-Unsubscribe') !== -1) ||
      (req.query && (req.query.unsubscribe === '1' || req.query.unsubscribe === 'true'));

    let patch = {};
    if (oneClick) {
      patch.subscribed = false;
    } else {
      const body = typeof req.body === 'string' ? safeJsonParse(req.body) : (req.body || {});
      if (typeof body.subscribed === 'boolean') patch.subscribed = body.subscribed;
      if (typeof body.weekly_digest === 'boolean') patch.weekly_digest = body.weekly_digest;
      if (!Object.keys(patch).length) return res.status(400).json({ error: 'Nothing to update' });
    }
    patch.updated_at = new Date().toISOString();

    const r = await fetch(`${base}?token=eq.${encodeURIComponent(token)}`, {
      method: 'PATCH',
      headers: { ...H, 'Content-Type': 'application/json', Prefer: 'return=representation' },
      body: JSON.stringify(patch)
    });
    if (!r.ok) return res.status(502).json({ error: 'Update failed', detail: await r.text() });
    const rows = await r.json();
    if (!Array.isArray(rows) || !rows.length) return res.status(404).json({ error: 'Not found' });
    return res.status(200).json(rows[0]);
  }

  res.setHeader('Allow', 'GET, POST');
  return res.status(405).json({ error: 'Method not allowed' });
}

function safeJsonParse(value) {
  try { return JSON.parse(value); } catch (_) { return {}; }
}
