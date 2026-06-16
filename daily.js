// Khatakshetra Daily — a 60-second katha + a guess-the-deity puzzle with a
// streak and a shareable result. Depends on site.js (loaded first) for the
// profile/XP/card helpers, but degrades gracefully if they are absent.
(function () {
  const DAILY_URL = 'content/daily.json?v=1';
  const MAX_ATTEMPTS = 5;

  let entry = null;
  let attempts = [];     // array of booleans: false = wrong, true = correct
  let cluesShown = 1;
  let finished = false;
  let solved = false;

  function pad(n) { return String(n).padStart(2, '0'); }
  function isoOf(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }
  function todayISO() { return isoOf(new Date()); }
  function yesterdayISO() { const d = new Date(); d.setDate(d.getDate() - 1); return isoOf(d); }
  function dayIndex() { return Math.floor((new Date() - new Date(2026, 0, 1)) / 86400000); }
  function norm(s) { return String(s || '').trim().toLowerCase().replace(/[^a-z0-9]/g, ''); }

  function pickEntry(list) {
    const t = todayISO();
    const exact = list.find((e) => e.date === t);
    if (exact) return exact;
    const i = ((dayIndex() % list.length) + list.length) % list.length;
    return list[i];
  }

  function dailyState() {
    if (typeof getKhatakshetraProfile !== 'function') return { streak: 0, lastDate: '', history: [] };
    const p = getKhatakshetraProfile();
    p.daily = p.daily || { streak: 0, lastDate: '', history: [] };
    return p.daily;
  }

  function recordCompletion() {
    const t = todayISO();
    let streak = 1;
    if (typeof getKhatakshetraProfile === 'function') {
      const p = getKhatakshetraProfile();
      p.daily = p.daily || { streak: 0, lastDate: '', history: [] };
      if (p.daily.lastDate !== t) {
        p.daily.streak = (p.daily.lastDate === yesterdayISO()) ? (p.daily.streak || 0) + 1 : 1;
        p.daily.lastDate = t;
        p.daily.history = (p.daily.history || []).concat([{ date: t, won: solved, tries: attempts.length }]).slice(-60);
        if (typeof saveKhatakshetraProfile === 'function') saveKhatakshetraProfile(p);
        if (typeof awardKhatakshetraProgress === 'function') {
          awardKhatakshetraProgress('daily_complete', {
            xp: solved ? 20 : 10,
            track: 'story_mastery',
            properties: { date: t, won: solved, tries: attempts.length }
          });
        }
      }
      streak = p.daily.streak;
    }
    return streak;
  }

  function resultGrid() {
    // One square per attempt: wrong = grey, the solving guess = green.
    return attempts.map((ok) => (ok ? '🟩' : '⬜')).join('');
  }

  function render() {
    const app = document.getElementById('dailyApp');
    if (!app || !entry) return;
    const st = dailyState();
    const clues = (entry.clues || []).slice(0, finished ? (entry.clues || []).length : cluesShown);
    app.innerHTML = `
      <article class="card featured">
        <div class="eyebrow">Today's Katha &middot; ${entry.date || todayISO()}</div>
        <h2>${entry.kathaTitle || 'A story for today'}</h2>
        <p>${entry.teaser || ''}</p>
        ${finished ? `<p><strong>Lesson:</strong> ${entry.lesson || ''}</p>` : ''}
      </article>

      <article class="card" style="margin-top:1rem">
        <div class="eyebrow">Daily Puzzle &middot; Guess the deity</div>
        <h3 id="puzzleStatus">${finished ? (solved ? 'Solved!' : 'Revealed') : `Clue ${cluesShown} of ${(entry.clues || []).length}`}</h3>
        <ul id="clueList">${clues.map((c) => `<li>${c}</li>`).join('')}</ul>
        <div id="attemptRow" style="font-size:1.4rem;letter-spacing:.15em;min-height:1.6rem">${resultGrid()}</div>
        ${finished ? renderFinished(st) : renderInput()}
      </article>
    `;
    if (!finished) {
      const form = document.getElementById('guessForm');
      if (form) form.addEventListener('submit', onGuess);
    } else {
      wireShare();
    }
  }

  function renderInput() {
    return `
      <form id="guessForm" class="signup-form" style="margin-top:.75rem">
        <label>Your guess
          <input id="guessInput" type="text" autocomplete="off" placeholder="A deity's name" required>
        </label>
        <button class="btn primary" type="submit">Guess</button>
      </form>
      <p class="fine-print" id="guessMsg"></p>
    `;
  }

  function renderFinished(st) {
    const answer = entry.answer || '';
    const share = `Khatakshetra Daily — ${entry.date || todayISO()}\n${solved ? `Guessed ${answer} in ${attempts.length}/${MAX_ATTEMPTS}` : `Stumped by ${answer}`} ${resultGrid()}\nStreak: ${st.streak} — play at https://khatakshetra.com/daily`;
    return `
      <p style="margin-top:.5rem"><strong>Answer:</strong> ${answer}${entry.deity ? '' : ''}</p>
      <div class="parampara-mini" style="margin:.5rem 0"><span>🔥 Streak ${st.streak}</span><span>${solved ? 'Solved' : 'Revealed'}</span></div>
      <div class="journey-actions">
        <a class="btn primary" id="waShare" target="_blank" rel="noopener">Share on WhatsApp</a>
        <button class="btn" type="button" id="copyShare">Copy result</button>
        <a class="btn" href="games.html">More quizzes</a>
      </div>
      <textarea id="shareText" readonly style="position:absolute;left:-9999px">${share}</textarea>
    `;
  }

  function wireShare() {
    const txt = document.getElementById('shareText');
    const wa = document.getElementById('waShare');
    if (wa && txt) wa.href = `https://wa.me/?text=${encodeURIComponent(txt.value)}`;
    const copy = document.getElementById('copyShare');
    if (copy && txt) {
      copy.addEventListener('click', function () {
        txt.select();
        try { document.execCommand('copy'); } catch (e) {}
        if (navigator.clipboard) navigator.clipboard.writeText(txt.value).catch(function () {});
        copy.textContent = 'Copied!';
        setTimeout(function () { copy.textContent = 'Copy result'; }, 1500);
      });
    }
  }

  function finish() {
    finished = true;
    const streak = recordCompletion();
    render();
    if (solved && entry.card && typeof revealTalapatraCard === 'function') {
      setTimeout(function () { revealTalapatraCard(entry.card); }, 300);
    }
    return streak;
  }

  function onGuess(e) {
    e.preventDefault();
    if (finished) return;
    const input = document.getElementById('guessInput');
    const guess = norm(input ? input.value : '');
    if (!guess) return;
    const accept = [entry.answer].concat(entry.accept || []).map(norm);
    const correct = accept.indexOf(guess) !== -1;
    attempts.push(correct);
    if (correct) { solved = true; finish(); return; }
    if (attempts.length >= MAX_ATTEMPTS) { solved = false; finish(); return; }
    cluesShown = Math.min((entry.clues || []).length, cluesShown + 1);
    render();
    const msg = document.getElementById('guessMsg');
    if (msg) msg.textContent = `Not quite — ${MAX_ATTEMPTS - attempts.length} guesses left. New clue revealed.`;
  }

  fetch(DAILY_URL)
    .then(function (r) { return r.json(); })
    .then(function (list) {
      if (!Array.isArray(list) || !list.length) return;
      entry = pickEntry(list);
      render();
    })
    .catch(function () {
      const app = document.getElementById('dailyApp');
      if (app) app.innerHTML = '<article class="card"><h3>Today’s puzzle is resting.</h3><p>Please check back soon.</p></article>';
    });
})();
