// First-party analytics sink (added for P0-2).
// Receives client events from trackKhatakshetraEvent() in site.js and inserts
// them into Supabase `user_events`. Analytics must never break the client, so
// this endpoint soft-fails (returns 200) whenever it cannot record an event.
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const body = typeof req.body === 'string' ? safeJsonParse(req.body) : req.body;
  const eventName = ((body && body.event_name) || '').toString().trim().slice(0, 80);
  if (!eventName) {
    return res.status(400).json({ error: 'Missing event_name' });
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;
  const table = process.env.SUPABASE_EVENTS_TABLE || 'user_events';

  // Soft no-op if the backend is not configured yet (keeps the client quiet).
  if (!supabaseUrl || !serviceRoleKey) {
    return res.status(200).json({ ok: false, skipped: 'not_configured' });
  }

  const anonymousId = body && body.anonymous_id ? String(body.anonymous_id).slice(0, 120) : null;
  const properties = body && typeof body.event_properties === 'object' && body.event_properties
    ? body.event_properties
    : {};

  const row = {
    anonymous_id: anonymousId,
    event_name: eventName,
    event_properties: properties
  };

  try {
    const resp = await fetch(`${supabaseUrl.replace(/\/$/, '')}/rest/v1/${table}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: serviceRoleKey,
        Authorization: `Bearer ${serviceRoleKey}`,
        Prefer: 'return=minimal'
      },
      body: JSON.stringify(row)
    });
    if (resp.ok) {
      return res.status(200).json({ ok: true });
    }
    const detail = await resp.text();
    return res.status(200).json({ ok: false, detail: detail });
  } catch (err) {
    return res.status(200).json({ ok: false, error: String(err) });
  }
}

function safeJsonParse(value) {
  try {
    return JSON.parse(value);
  } catch (_) {
    return null;
  }
}
