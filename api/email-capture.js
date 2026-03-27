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

  const baseUrl = `${supabaseUrl.replace(/\/$/, '')}/rest/v1/${table}`;
  const upsertResp = await fetch(`${baseUrl}?on_conflict=email_id,cta`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: serviceRoleKey,
      Authorization: `Bearer ${serviceRoleKey}`,
      Prefer: 'resolution=merge-duplicates,return=minimal'
    },
    body: JSON.stringify({ email_id: email, cta: cta })
  });

  if (upsertResp.ok) {
    return res.status(200).json({ ok: true });
  }

  const upsertErrorText = await upsertResp.text();
  // If no matching unique/exclusion constraint exists for on_conflict,
  // fall back to a plain insert so capture still works.
  if (upsertResp.status === 400 && upsertErrorText.includes('42P10')) {
    const insertResp = await fetch(baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: serviceRoleKey,
        Authorization: `Bearer ${serviceRoleKey}`,
        Prefer: 'return=minimal'
      },
      body: JSON.stringify({ email_id: email, cta: cta })
    });

    if (insertResp.ok) {
      return res.status(200).json({ ok: true, mode: 'insert' });
    }

    const insertErrorText = await insertResp.text();
    if (insertResp.status === 409 && isDuplicateConflict(insertErrorText)) {
      // Duplicate email+cta should be considered success for signup UX.
      return res.status(200).json({ ok: true, mode: 'duplicate' });
    }
    return res.status(insertResp.status).json({
      error: 'Supabase insert failed',
      status: insertResp.status,
      detail: insertErrorText
    });
  }

  if (upsertResp.status === 409 && isDuplicateConflict(upsertErrorText)) {
    // Duplicate email+cta should be considered success for signup UX.
    return res.status(200).json({ ok: true, mode: 'duplicate' });
  }

  return res.status(upsertResp.status).json({
    error: 'Supabase insert failed',
    status: upsertResp.status,
    detail: upsertErrorText
  });
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

function isDuplicateConflict(errorText) {
  const text = String(errorText || '');
  return text.includes('duplicate key value violates unique constraint');
}

function safeJsonParse(value) {
  try {
    return JSON.parse(value);
  } catch (_) {
    return null;
  }
}
