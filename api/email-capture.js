export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const body = typeof req.body === 'string' ? safeJsonParse(req.body) : req.body;
  const email = ((body && body.email_id) || '').trim().toLowerCase();
  const cta = ((body && body.cta) || '').trim();

  if (!isValidEmail(email)) {
    return res.status(400).json({ error: 'Invalid email' });
  }

  const allowedCtas = new Set(['main_page', 'kids_coloring_book']);
  if (!allowedCtas.has(cta)) {
    return res.status(400).json({ error: 'Invalid cta' });
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const table = process.env.SUPABASE_EMAIL_TABLE || 'email_captures';

  if (!supabaseUrl || !serviceRoleKey) {
    return res.status(500).json({ error: 'Server is not configured' });
  }

  const endpoint = `${supabaseUrl.replace(/\/$/, '')}/rest/v1/${table}`;
  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: serviceRoleKey,
      Authorization: `Bearer ${serviceRoleKey}`,
      Prefer: 'resolution=merge-duplicates,return=minimal'
    },
    body: JSON.stringify({ email_id: email, cta: cta })
  });

  if (!resp.ok) {
    const errorText = await resp.text();
    return res.status(500).json({ error: 'Supabase insert failed', detail: errorText });
  }

  return res.status(200).json({ ok: true });
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function safeJsonParse(value) {
  try {
    return JSON.parse(value);
  } catch (_) {
    return null;
  }
}
