export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const body = typeof req.body === 'string' ? safeJsonParse(req.body) : req.body;
  const email = ((body && body.email_id) || '').trim().toLowerCase();
  const ctaRaw = ((body && body.cta) || '').trim();
  const cta = normalizeCta(ctaRaw);

  if (!isValidEmail(email)) {
    return res.status(400).json({ error: 'Invalid email' });
  }

  if (!cta) {
    return res.status(400).json({ error: 'Invalid cta' });
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;
  const table = process.env.SUPABASE_EMAIL_TABLE || 'email_captures';

  if (!supabaseUrl || !serviceRoleKey) {
    return res.status(500).json({
      error: 'Server is not configured',
      missing: {
        SUPABASE_URL: !supabaseUrl,
        SUPABASE_SERVICE_ROLE_KEY_or_SUPABASE_SECRET_KEY: !serviceRoleKey
      }
    });
  }

  const endpoint = `${supabaseUrl.replace(/\/$/, '')}/rest/v1/${table}?on_conflict=email_id,cta`;
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
    return res.status(resp.status).json({
      error: 'Supabase insert failed',
      status: resp.status,
      detail: errorText
    });
  }

  return res.status(200).json({ ok: true });
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function normalizeCta(value) {
  const key = String(value || '').trim().toLowerCase().replace(/\s+/g, '_').replace(/-/g, '_');
  if (key === 'main_page' || key === 'main') return 'main_page';
  if (key === 'kids_coloring_book' || key === 'kids_colouring_book' || key === 'coloring_book') {
    return 'kids_coloring_book';
  }
  return '';
}

function safeJsonParse(value) {
  try {
    return JSON.parse(value);
  } catch (_) {
    return null;
  }
}
