const KHATAKSHETRA_PROFILE_KEY = 'khatakshetra_profile';
const KHATAKSHETRA_SIGNUPS_KEY = 'khatakshetra_signups';

const KHATAKSHETRA_TITLES = [
  { level: 1, min: 0, title: 'Shravaka', meaning: 'The Listener' },
  { level: 2, min: 80, title: 'Jigyasu', meaning: 'The Curious' },
  { level: 3, min: 220, title: 'Sadhaka', meaning: 'The Seeker' },
  { level: 4, min: 420, title: 'Katha Vachak', meaning: 'The Storyteller' },
  { level: 5, min: 750, title: 'Vidwan', meaning: 'The Learned' },
  { level: 6, min: 1200, title: 'Acharya', meaning: 'The Teacher' }
];

let pendingSignupCta = 'site_signup';
let pendingSignupCallback = null;

// ---------------------------------------------------------------------------
// Analytics (added for P0-2). Wired site-wide via site.js so every page is
// covered without editing each HTML file. No-op until the IDs below are set,
// so this is safe to deploy with empty values.
// ---------------------------------------------------------------------------
const KHATAKSHETRA_ANALYTICS = {
  ga4Id: '',            // e.g. 'G-XXXXXXXXXX'  (Google Analytics 4 Measurement ID)
  posthogKey: '',       // e.g. 'phc_xxxxxxxx'  (PostHog project API key)
  posthogHost: 'https://us.i.posthog.com'
};
let khatakshetraAnalyticsReady = false;

function initKhatakshetraAnalytics() {
  if (khatakshetraAnalyticsReady) return;
  khatakshetraAnalyticsReady = true;
  // Google Analytics 4
  if (KHATAKSHETRA_ANALYTICS.ga4Id && KHATAKSHETRA_ANALYTICS.ga4Id.indexOf('G-') === 0) {
    const tag = document.createElement('script');
    tag.async = true;
    tag.src = `https://www.googletagmanager.com/gtag/js?id=${KHATAKSHETRA_ANALYTICS.ga4Id}`;
    document.head.appendChild(tag);
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', KHATAKSHETRA_ANALYTICS.ga4Id);
  }
  // PostHog (loaded from CDN; init on load)
  if (KHATAKSHETRA_ANALYTICS.posthogKey && KHATAKSHETRA_ANALYTICS.posthogKey.indexOf('phc_') === 0) {
    const ph = document.createElement('script');
    ph.async = true;
    ph.src = 'https://cdn.jsdelivr.net/npm/posthog-js@1/dist/array.full.js';
    ph.onload = function () {
      if (window.posthog && typeof window.posthog.init === 'function') {
        window.posthog.init(KHATAKSHETRA_ANALYTICS.posthogKey, {
          api_host: KHATAKSHETRA_ANALYTICS.posthogHost,
          person_profiles: 'identified_only'
        });
      }
    };
    document.head.appendChild(ph);
  }
}

// Send one event to GA4, PostHog, and first-party Supabase (/api/event).
// Every channel is wrapped so analytics can never break the page.
function trackKhatakshetraEvent(eventName, properties) {
  properties = properties || {};
  try { if (window.gtag) window.gtag('event', eventName, properties); } catch (e) {}
  try { if (window.posthog && window.posthog.capture) window.posthog.capture(eventName, properties); } catch (e) {}
  try {
    const raw = JSON.parse(localStorage.getItem(KHATAKSHETRA_PROFILE_KEY) || 'null');
    fetch('/api/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_name: eventName,
        anonymous_id: raw && raw.anonymous_id ? raw.anonymous_id : null,
        event_properties: properties
      }),
      keepalive: true
    }).catch(function () {});
  } catch (e) {}
}

function getKhatakshetraProfile() {
  const existing = JSON.parse(localStorage.getItem(KHATAKSHETRA_PROFILE_KEY) || 'null');
  if (existing && existing.anonymous_id) {
    existing.tracks = existing.tracks || {};
    existing.unlocks = existing.unlocks || [];
    existing.events = existing.events || [];
    existing.cards = existing.cards || [];
    existing.child_name = existing.child_name || '';
    return existing;
  }
  const created = {
    anonymous_id: `anon_${Date.now()}_${Math.random().toString(16).slice(2)}`,
    email: '',
    child_name: '',
    xp: 0,
    level: 1,
    tracks: {
      story_mastery: 0,
      creative_practice: 0,
      temple_seva: 0,
      community: 0
    },
    unlocks: [],
    cards: [],
    events: [],
    created_at: new Date().toISOString()
  };
  localStorage.setItem(KHATAKSHETRA_PROFILE_KEY, JSON.stringify(created));
  return created;
}

function saveKhatakshetraProfile(profile) {
  profile.level = getLevelForXp(profile.xp || 0);
  localStorage.setItem(KHATAKSHETRA_PROFILE_KEY, JSON.stringify(profile));
  renderKhatakshetraProgressChip();
  // P1-2: if signed in, push the updated profile to Supabase (debounced).
  khatakshetraQueueProgressPush();
  return profile;
}

function getLevelForXp(xp) {
  if (xp >= 1200) return 6;
  if (xp >= 750) return 5;
  if (xp >= 420) return 4;
  if (xp >= 220) return 3;
  if (xp >= 80) return 2;
  return 1;
}

function getKhatakshetraTitle(levelOrXp) {
  const level = typeof levelOrXp === 'number' && levelOrXp > 6 ? getLevelForXp(levelOrXp) : levelOrXp;
  return KHATAKSHETRA_TITLES.find((item) => item.level === level) || KHATAKSHETRA_TITLES[0];
}

function awardKhatakshetraProgress(eventName, options = {}) {
  const points = {
    quiz_answer_correct: 10,
    quiz_complete: 50,
    family_room_complete: 75,
    coloring_open: 15,
    coloring_download: 40,
    booklet_print: 60,
    journey_node_complete: 20,
    journey_complete: 120,
    temple_tip_saved: 80,
    referral_saved: 120
  };
  const trackMap = {
    quiz_answer_correct: 'story_mastery',
    quiz_complete: 'story_mastery',
    family_room_complete: 'community',
    coloring_open: 'creative_practice',
    coloring_download: 'creative_practice',
    booklet_print: 'story_mastery',
    journey_node_complete: 'story_mastery',
    journey_complete: 'story_mastery',
    temple_tip_saved: 'temple_seva',
    referral_saved: 'community'
  };
  const profile = getKhatakshetraProfile();
  const xp = options.xp || points[eventName] || 0;
  const track = options.track || trackMap[eventName] || 'story_mastery';
  profile.xp = (profile.xp || 0) + xp;
  profile.tracks[track] = (profile.tracks[track] || 0) + xp;
  if (options.unlock && !profile.unlocks.includes(options.unlock)) profile.unlocks.push(options.unlock);
  profile.events.push({
    event_name: eventName,
    xp,
    track,
    unlock: options.unlock || '',
    properties: options.properties || {},
    created_at: new Date().toISOString()
  });
  // P0-2: also emit the event to analytics (GA4 / PostHog / first-party).
  trackKhatakshetraEvent(eventName, Object.assign({ xp: xp, track: track, unlock: options.unlock || '' }, options.properties || {}));
  if (options.card) addTalapatraCard(options.card, profile);
  return saveKhatakshetraProfile(profile);
}

function addTalapatraCard(card, profileArg) {
  if (!card || !card.id) return { profile: getKhatakshetraProfile(), isNew: false };
  const profile = profileArg || getKhatakshetraProfile();
  profile.cards = profile.cards || [];
  const exists = profile.cards.some((item) => item.id === card.id);
  if (!exists) {
    profile.cards.push({
      ...card,
      earned_at: new Date().toISOString()
    });
  }
  if (!profileArg) saveKhatakshetraProfile(profile);
  return { profile, isNew: !exists };
}

function getTalapatraCardForQuiz(quizSlug, pct) {
  const catalog = {
    'rama-navami-beginner': {
      common: { id: 'rama-prince-common', title: 'Rama', subtitle: 'The Prince of Dharma', rarity: 'common', quote: 'A promise becomes sacred when it costs something.' },
      rare: { id: 'sita-chosen-rare', title: 'Sita', subtitle: 'The Chosen Strength', rarity: 'rare', quote: 'Grace can be gentle and unshakable at once.' },
      epic: { id: 'hanuman-devoted-epic', title: 'Hanuman', subtitle: 'Strength That Kneels', rarity: 'epic', quote: 'True power remembers whom it serves.' }
    },
    'shani-dev-beginner': {
      common: { id: 'shani-time-common', title: 'Shani Dev', subtitle: 'The Slow Teacher', rarity: 'common', quote: 'Delay can become discipline.' },
      rare: { id: 'dasharatha-courage-rare', title: 'Dasharatha', subtitle: 'The King Who Stood Before Saturn', rarity: 'rare', quote: 'Courage protects more than itself.' },
      epic: { id: 'shani-karma-epic', title: 'Shani Dev', subtitle: 'Karma Made Visible', rarity: 'epic', quote: 'What is true does not need to hurry.' }
    },
    'ganesha-beginner': {
      common: { id: 'ganesha-beginning-common', title: 'Ganesha', subtitle: 'Before Every Beginning', rarity: 'common', quote: 'Wisdom begins by making space.' },
      rare: { id: 'parvati-boundary-rare', title: 'Parvati', subtitle: 'The Mother Who Creates', rarity: 'rare', quote: 'Love can set a boundary.' },
      epic: { id: 'ganesha-vighnaharta-epic', title: 'Vighnaharta', subtitle: 'The Remover', rarity: 'epic', quote: 'Some obstacles teach before they leave.' }
    },
    'dashavatara-beginner': {
      common: { id: 'matsya-common', title: 'Matsya', subtitle: 'The First Rescue', rarity: 'common', quote: 'Wisdom survives when it is carried carefully.' },
      rare: { id: 'vamana-rare', title: 'Vamana', subtitle: 'The Small Form With Vast Steps', rarity: 'rare', quote: 'Humility can measure the universe.' },
      epic: { id: 'vishnu-preserver-epic', title: 'Vishnu', subtitle: 'The Preserver Across Ages', rarity: 'epic', quote: 'Dharma returns in the form the age needs.' }
    }
  };
  const fallback = {
    common: { id: `${quizSlug}-common`, title: 'Story Seeker', subtitle: 'First Understanding', rarity: 'common', quote: 'Every answer lights one more path.' },
    rare: { id: `${quizSlug}-rare`, title: 'Story Keeper', subtitle: 'Clear Understanding', rarity: 'rare', quote: 'Remembering is also a form of devotion.' },
    epic: { id: `${quizSlug}-epic`, title: 'Katha Vachak', subtitle: 'Mastered Round', rarity: 'epic', quote: 'A story lives fully when it can be retold.' }
  };
  const cards = catalog[quizSlug] || fallback;
  if (pct >= 100) return cards.epic;
  if (pct >= 80) return cards.rare;
  return cards.common;
}

function ensureKhatakshetraShell() {
  if (!document.getElementById('khatakshetraProgressChip')) {
    const chip = document.createElement('button');
    chip.id = 'khatakshetraProgressChip';
    chip.className = 'progress-chip';
    chip.type = 'button';
    chip.addEventListener('click', () => {
      const profile = getKhatakshetraProfile();
      if (profile.email) window.location.href = 'sangraha.html';
      else localSignupIntent('progress_chip');
    });
    document.body.appendChild(chip);
  }

  if (!document.getElementById('khatakshetraSignupModal')) {
    const modal = document.createElement('div');
    modal.id = 'khatakshetraSignupModal';
    modal.className = 'modal-backdrop';
    modal.setAttribute('aria-hidden', 'true');
    modal.innerHTML = `
      <div class="signup-modal" role="dialog" aria-modal="true" aria-labelledby="signupTitle">
        <button class="modal-close" type="button" data-close-signup aria-label="Close">x</button>
        <div class="eyebrow">Save your journey</div>
        <h2 id="signupTitle">Keep the story path alive.</h2>
        <p>Save progress, unlock the next story drop, and get first access to family challenges and festival kit updates.</p>
        <form id="khatakshetraSignupForm" class="signup-form">
          <label>Child or family name <input id="signupChildName" type="text" autocomplete="name" placeholder="Example: Anika or Rao family"></label>
          <label>Email <input id="signupEmail" type="email" autocomplete="email" required placeholder="you@example.com"></label>
          <button class="btn primary" type="submit">Save Progress</button>
        </form>
        <p class="fine-print">We will use this to preserve your unlocks and send the next story, challenge, or kit update.</p>
      </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (event) => {
      if (event.target === modal || event.target.matches('[data-close-signup]')) closeKhatakshetraSignupModal();
    });
    document.getElementById('khatakshetraSignupForm').addEventListener('submit', saveKhatakshetraSignupFromModal);
  }

  if (!document.getElementById('khatakshetraCardReveal')) {
    const reveal = document.createElement('div');
    reveal.id = 'khatakshetraCardReveal';
    reveal.className = 'modal-backdrop';
    reveal.setAttribute('aria-hidden', 'true');
    reveal.innerHTML = `
      <div class="talapatra-reveal" role="dialog" aria-modal="true" aria-labelledby="cardRevealTitle">
        <button class="modal-close" type="button" data-close-card aria-label="Close">x</button>
        <div class="eyebrow">Talapatra card earned</div>
        <div class="talapatra-prize" id="talapatraPrize"></div>
        <div class="card-actions">
          <a class="btn primary" href="sangraha.html">Open Sangraha</a>
          <button class="btn" type="button" data-close-card>Continue</button>
        </div>
      </div>
    `;
    document.body.appendChild(reveal);
    reveal.addEventListener('click', (event) => {
      if (event.target === reveal || event.target.matches('[data-close-card]')) closeTalapatraReveal();
    });
  }
}

function localSignupIntent(cta, options = {}) {
  openKhatakshetraSignupModal(cta, options);
}

function openKhatakshetraSignupModal(cta, options = {}) {
  ensureKhatakshetraShell();
  const profile = getKhatakshetraProfile();
  pendingSignupCta = cta || 'site_signup';
  pendingSignupCallback = typeof options.afterSave === 'function' ? options.afterSave : null;
  document.getElementById('signupChildName').value = profile.child_name || '';
  document.getElementById('signupEmail').value = profile.email || '';
  const modal = document.getElementById('khatakshetraSignupModal');
  modal.classList.add('is-open');
  modal.setAttribute('aria-hidden', 'false');
  setTimeout(() => document.getElementById(profile.email ? 'signupChildName' : 'signupEmail').focus(), 40);
}

function closeKhatakshetraSignupModal() {
  const modal = document.getElementById('khatakshetraSignupModal');
  if (!modal) return;
  modal.classList.remove('is-open');
  modal.setAttribute('aria-hidden', 'true');
}

function saveKhatakshetraSignupFromModal(event) {
  event.preventDefault();
  const email = document.getElementById('signupEmail').value.trim();
  const childName = document.getElementById('signupChildName').value.trim();
  if (!email) return;
  const profile = getKhatakshetraProfile();
  profile.email = email;
  profile.child_name = childName;
  profile.last_cta = pendingSignupCta;
  profile.events.push({
    event_name: 'signup_intent_saved',
    xp: 0,
    track: 'community',
    unlock: '',
    properties: { cta: pendingSignupCta, child_name: childName },
    created_at: new Date().toISOString()
  });
  saveKhatakshetraProfile(profile);

  const existing = JSON.parse(localStorage.getItem(KHATAKSHETRA_SIGNUPS_KEY) || '[]');
  existing.push({ email, child_name: childName, cta: pendingSignupCta, captured_at: new Date().toISOString() });
  localStorage.setItem(KHATAKSHETRA_SIGNUPS_KEY, JSON.stringify(existing));

  // P0-1: actually send the signup to the server. Previously this modal saved
  // only to localStorage, so in-product signups never reached Supabase.
  fetch('/api/email-capture', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email_id: email, cta: pendingSignupCta, child_name: childName })
  }).catch(function () {});
  trackKhatakshetraEvent('signup_intent_saved', { cta: pendingSignupCta });

  // P1-1: also send a magic link so progress can sync across devices. No-op
  // until Supabase is provisioned. The email capture above still works either way.
  khatakshetraSupabaseSignIn(email);

  closeKhatakshetraSignupModal();
  if (pendingSignupCallback) pendingSignupCallback(profile);
  pendingSignupCallback = null;
}

function renderKhatakshetraProgress(targetId) {
  const target = document.getElementById(targetId);
  if (!target) return;
  const profile = getKhatakshetraProfile();
  const title = getKhatakshetraTitle(profile.level);
  target.innerHTML = `
    <article class="card featured">
      <div class="eyebrow">Your Parampara Tree</div>
      <h2>${title.title} · ${profile.xp} XP</h2>
      <p>${profile.email ? `Progress linked to ${profile.email}.` : 'Play now, then add email to preserve your unlocks and get new story drops.'}</p>
      <div class="tag-row">
        <span class="tag">Story ${profile.tracks.story_mastery || 0}</span>
        <span class="tag">Creative ${profile.tracks.creative_practice || 0}</span>
        <span class="tag">Temple ${profile.tracks.temple_seva || 0}</span>
        <span class="tag">Community ${profile.tracks.community || 0}</span>
        <span class="tag">Cards ${(profile.cards || []).length}</span>
      </div>
    </article>
  `;
}

function renderKhatakshetraProgressChip() {
  const chip = document.getElementById('khatakshetraProgressChip');
  if (!chip) return;
  const profile = getKhatakshetraProfile();
  const title = getKhatakshetraTitle(profile.level);
  chip.innerHTML = `<span>${title.title}</span><strong>${profile.xp} XP</strong>`;
}

function revealTalapatraCard(card) {
  if (!card || !card.id) return;
  ensureKhatakshetraShell();
  const result = addTalapatraCard(card);
  const storedCard = result.profile.cards.find((item) => item.id === card.id) || card;
  const prize = document.getElementById('talapatraPrize');
  prize.innerHTML = `
    <div class="card-rarity ${storedCard.rarity || 'common'}">${storedCard.rarity || 'common'}</div>
    <h2 id="cardRevealTitle">${storedCard.title}</h2>
    <h3>${storedCard.subtitle || 'Story Card'}</h3>
    <p>${storedCard.quote || 'A story remembered becomes a light for the next path.'}</p>
    <small>${result.isNew ? 'Added to your Sangraha.' : 'Already in your Sangraha.'}</small>
  `;
  const modal = document.getElementById('khatakshetraCardReveal');
  modal.classList.add('is-open');
  modal.setAttribute('aria-hidden', 'false');
}

function closeTalapatraReveal() {
  const modal = document.getElementById('khatakshetraCardReveal');
  if (!modal) return;
  modal.classList.remove('is-open');
  modal.setAttribute('aria-hidden', 'true');
}

// ---------------------------------------------------------------------------
// Supabase auth + cross-device progress sync (P1-1 / P1-2).
// Entirely additive and graceful: if /api/public-config reports the project is
// not configured (env vars unset), every function below quietly no-ops, so the
// site behaves exactly as before. Once provisioned + RLS applied, a magic-link
// sign-in links the local anonymous profile to a real user and keeps XP,
// streaks, unlocks, and the Sangraha in sync across devices.
// ---------------------------------------------------------------------------
let khatakshetraSupabase = null;
let khatakshetraSupabaseInit = null;     // promise, so we init once
let khatakshetraSyncedUserId = null;
let khatakshetraPushTimer = null;

function khatakshetraLoadScript(src) {
  return new Promise(function (resolve, reject) {
    const s = document.createElement('script');
    s.src = src;
    s.async = true;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

function initKhatakshetraSupabase() {
  if (khatakshetraSupabaseInit) return khatakshetraSupabaseInit;
  khatakshetraSupabaseInit = (async function () {
    try {
      const res = await fetch('/api/public-config');
      if (!res.ok) return null;
      const cfg = await res.json();
      if (!cfg || !cfg.configured || !cfg.supabaseUrl || !cfg.supabaseAnonKey) return null;
      if (!(window.supabase && window.supabase.createClient)) {
        await khatakshetraLoadScript('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js');
      }
      khatakshetraSupabase = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
      });
      khatakshetraSupabase.auth.onAuthStateChange(function (_event, session) {
        if (session && session.user) khatakshetraOnSignedIn(session.user);
      });
      const sess = await khatakshetraSupabase.auth.getSession();
      if (sess && sess.data && sess.data.session && sess.data.session.user) {
        khatakshetraOnSignedIn(sess.data.session.user);
      }
      return khatakshetraSupabase;
    } catch (e) {
      return null;
    }
  })();
  return khatakshetraSupabaseInit;
}

async function khatakshetraSupabaseSignIn(email) {
  if (!email) return false;
  const client = await initKhatakshetraSupabase();
  if (!client) return false; // not configured yet — email capture already handled it
  try {
    await client.auth.signInWithOtp({ email: email, options: { emailRedirectTo: window.location.href } });
    return true;
  } catch (e) {
    return false;
  }
}

async function khatakshetraOnSignedIn(user) {
  if (!khatakshetraSupabase || !user || khatakshetraSyncedUserId === user.id) return;
  khatakshetraSyncedUserId = user.id;
  const profile = getKhatakshetraProfile();
  try {
    await khatakshetraSupabase.from('app_users').upsert(
      { id: user.id, email: user.email || profile.email || null, full_name: profile.child_name || null },
      { onConflict: 'id' }
    );
    const remote = await khatakshetraSupabase
      .from('user_progress').select('*').eq('user_id', user.id).maybeSingle();
    const merged = mergeKhatakshetraProgress(profile, remote && remote.data);
    saveKhatakshetraProfile(merged);               // also queues a push
    await khatakshetraPushProgress(user.id, merged);
  } catch (e) {
    /* keep local copy; never break the page */
  }
}

function mergeKhatakshetraProgress(local, remote) {
  if (!remote) return local;
  const out = local;
  out.xp = Math.max(local.xp || 0, remote.xp || 0);
  out.level = getLevelForXp(out.xp);
  out.tracks = out.tracks || {};
  const rt = remote.tracks || {};
  ['story_mastery', 'creative_practice', 'temple_seva', 'community'].forEach(function (k) {
    out.tracks[k] = Math.max((out.tracks && out.tracks[k]) || 0, rt[k] || 0);
  });
  out.unlocks = Array.from(new Set([].concat(local.unlocks || [], remote.unlocks || [])));
  const byId = {};
  [].concat(local.cards || [], remote.cards || []).forEach(function (c) { if (c && c.id) byId[c.id] = c; });
  out.cards = Object.keys(byId).map(function (k) { return byId[k]; });
  const localStreak = (local.daily && local.daily.streak) || 0;
  const remoteStreak = (remote.daily && remote.daily.streak) || 0;
  out.daily = (remoteStreak > localStreak ? remote.daily : local.daily) || out.daily || { streak: 0, lastDate: '', history: [] };
  return out;
}

async function khatakshetraPushProgress(userId, profile) {
  if (!khatakshetraSupabase || !userId) return;
  try {
    await khatakshetraSupabase.from('user_progress').upsert({
      user_id: userId,
      anonymous_id: profile.anonymous_id || null,
      xp: profile.xp || 0,
      level: profile.level || 1,
      tracks: profile.tracks || {},
      unlocks: profile.unlocks || [],
      cards: profile.cards || [],
      daily: profile.daily || {},
      last_activity_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }, { onConflict: 'user_id' });
  } catch (e) {
    /* ignore — localStorage remains the source of truth offline */
  }
}

// Debounced: when a signed-in user earns XP, persist it without hammering the DB.
function khatakshetraQueueProgressPush() {
  if (!khatakshetraSyncedUserId) return;
  clearTimeout(khatakshetraPushTimer);
  khatakshetraPushTimer = setTimeout(function () {
    khatakshetraPushProgress(khatakshetraSyncedUserId, getKhatakshetraProfile());
  }, 1500);
}

// Shared footer: ensures every page that loads site.js carries a consistent set
// of footer links (incl. About + Contact). Non-destructive — appends a links row
// to the page's existing <footer>. Skips if static footer links already exist
// (e.g. generated SEO pages, which print .site-footer-links server-side).
function injectKhatakshetraFooter() {
  if (document.querySelector('.kx-footer-links') || document.querySelector('.site-footer-links')) return;
  var links = [
    ['/', 'Home'], ['/stories', 'Stories'], ['/games', 'Play'], ['/temples', 'Temples'],
    ['/daily', 'Daily'], ['/kits', 'Kits'], ['/about', 'About'], ['/contact', 'Contact']
  ];
  var bar = document.createElement('nav');
  bar.className = 'kx-footer-links';
  bar.setAttribute('aria-label', 'Footer');
  bar.style.cssText = 'text-align:center;padding:1.25rem 1rem;font-size:0.9rem;line-height:2.1;border-top:1px solid rgba(200,150,44,0.18);';
  bar.innerHTML = links.map(function (l) {
    return '<a href="' + l[0] + '" style="color:#C8962C;text-decoration:none;margin:0 0.5rem;white-space:nowrap;">' + l[1] + '</a>';
  }).join('<span style="opacity:.4">&middot;</span>');
  var foot = document.querySelector('footer');
  (foot || document.body).appendChild(bar);
}

document.addEventListener('DOMContentLoaded', () => {
  ensureKhatakshetraShell();
  renderKhatakshetraProgressChip();
  initKhatakshetraAnalytics();
  initKhatakshetraSupabase();
  injectKhatakshetraFooter();
});
