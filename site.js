function localSignupIntent(cta) {
  const email = window.prompt('Enter email to save your unlocks and get the next story drop:');
  if (!email) return;
  const profile = getKhatakshetraProfile();
  profile.email = email;
  profile.last_cta = cta;
  localStorage.setItem('khatakshetra_profile', JSON.stringify(profile));
  const key = 'khatakshetra_signups';
  const existing = JSON.parse(localStorage.getItem(key) || '[]');
  existing.push({ email, cta, captured_at: new Date().toISOString() });
  localStorage.setItem(key, JSON.stringify(existing));
  window.alert('You are in. Your progress is saved here, and new story drops will be sent to your email.');
}

function getKhatakshetraProfile() {
  const key = 'khatakshetra_profile';
  const existing = JSON.parse(localStorage.getItem(key) || 'null');
  if (existing && existing.anonymous_id) return existing;
  const created = {
    anonymous_id: `anon_${Date.now()}_${Math.random().toString(16).slice(2)}`,
    email: '',
    xp: 0,
    level: 1,
    tracks: {
      story_mastery: 0,
      creative_practice: 0,
      temple_seva: 0,
      community: 0
    },
    unlocks: [],
    events: [],
    created_at: new Date().toISOString()
  };
  localStorage.setItem(key, JSON.stringify(created));
  return created;
}

function getLevelForXp(xp) {
  if (xp >= 1200) return 6;
  if (xp >= 750) return 5;
  if (xp >= 420) return 4;
  if (xp >= 220) return 3;
  if (xp >= 80) return 2;
  return 1;
}

function awardKhatakshetraProgress(eventName, options = {}) {
  const points = {
    quiz_answer_correct: 10,
    quiz_complete: 50,
    family_room_complete: 75,
    coloring_open: 15,
    coloring_download: 40,
    booklet_print: 60,
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
    temple_tip_saved: 'temple_seva',
    referral_saved: 'community'
  };
  const profile = getKhatakshetraProfile();
  const xp = options.xp || points[eventName] || 0;
  const track = options.track || trackMap[eventName] || 'story_mastery';
  profile.xp += xp;
  profile.tracks[track] = (profile.tracks[track] || 0) + xp;
  profile.level = getLevelForXp(profile.xp);
  if (options.unlock && !profile.unlocks.includes(options.unlock)) profile.unlocks.push(options.unlock);
  profile.events.push({
    event_name: eventName,
    xp,
    track,
    unlock: options.unlock || '',
    properties: options.properties || {},
    created_at: new Date().toISOString()
  });
  localStorage.setItem('khatakshetra_profile', JSON.stringify(profile));
  return profile;
}

function renderKhatakshetraProgress(targetId) {
  const target = document.getElementById(targetId);
  if (!target) return;
  const profile = getKhatakshetraProfile();
  target.innerHTML = `
    <article class="card featured">
      <div class="eyebrow">Your Progress</div>
      <h2>Level ${profile.level} · ${profile.xp} XP</h2>
      <p>${profile.email ? `Progress linked to ${profile.email}.` : 'Play now, then add email to preserve your unlocks and get new story drops.'}</p>
      <div class="tag-row">
        <span class="tag">Story ${profile.tracks.story_mastery || 0}</span>
        <span class="tag">Creative ${profile.tracks.creative_practice || 0}</span>
        <span class="tag">Temple ${profile.tracks.temple_seva || 0}</span>
        <span class="tag">Community ${profile.tracks.community || 0}</span>
      </div>
    </article>
  `;
}
