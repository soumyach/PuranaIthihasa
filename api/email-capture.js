export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const body = typeof req.body === 'string' ? safeJsonParse(req.body) : req.body;
  const email = ((body && body.email_id) || '').trim().toLowerCase();
  const ctaRaw = ((body && body.cta) || '').trim();
  const cta = normalizeCta(ctaRaw);
  // P0-1: capture the child/family name the in-product modal collects.
  const childName = ((body && body.child_name) || '').toString().trim().slice(0, 120);

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

  // Only attach metadata when we actually have some, so duplicate upserts do
  // not clobber a previously stored name with an empty object.
  const row = { email_id: email, cta: cta };
  if (childName) row.metadata = { child_name: childName };

  const baseUrl = `${supabaseUrl.replace(/\/$/, '')}/rest/v1/${table}`;
  const upsertResp = await fetch(`${baseUrl}?on_conflict=email_id,cta`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: serviceRoleKey,
      Authorization: `Bearer ${serviceRoleKey}`,
      Prefer: 'resolution=merge-duplicates,return=minimal'
    },
    body: JSON.stringify(row)
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
      body: JSON.stringify(row)
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
  if (key === 'starter_story_kit' || key === 'free_story_kit') return 'starter_story_kit';
  if (key === 'temple_updates' || key === 'temple_guides') return 'temple_updates';
  if (key === 'festival_challenge') return 'festival_challenge';
  if (key === 'community_contributor' || key === 'community') return 'community_contributor';
  if (key === 'pdf_storybook') return 'pdf_storybook';
  if (key === 'mahabharata_interest') return 'mahabharata_interest';
  if (key === 'gita_interest') return 'gita_interest';
  if (key === 'shani_story_interest') return 'shani_story_interest';
  if (key === 'ganesha_story_interest') return 'ganesha_story_interest';
  if (key === 'dashavatara_interest') return 'dashavatara_interest';
  if (key === 'deity_hub_vote') return 'deity_hub_vote';
  if (key === 'temple_updates_hyderabad') return 'temple_updates_hyderabad';
  if (key === 'ganesh_kit' || key === 'ganesh_chaturthi_kit') return 'ganesh_kit';
  if (key === 'rath_yatra_kit' || key === 'rath_kit') return 'rath_yatra_kit';
  if (key === 'raksha_janmashtami_kit' || key === 'raksha_bandhan_janmashtami_kit') {
    return 'raksha_janmashtami_kit';
  }
  if (key === 'quiz_rama_navami') return 'quiz_rama_navami';
  if (key === 'quiz_shani_dev') return 'quiz_shani_dev';
  if (key === 'school_bulk') return 'school_bulk';
  if (key === 'nri_family') return 'nri_family';
  // P0-1: previously any unlisted CTA returned '' and was rejected with 400.
  // That dropped every in-product signup (quiz_unlock, progress_chip,
  // ramayana_journey_save, family_quiz_room, temple_tip_*, festival_calendar,
  // site_signup, ...). Accept any safe slug so those captures are saved.
  if (/^[a-z0-9_]{2,40}$/.test(key)) return key;
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
