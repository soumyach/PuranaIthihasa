// Khatakshetra Daily — a 60-second katha + a guess-the-deity puzzle with a
// streak and a shareable result. Depends on site.js (loaded first) for the
// profile/XP/card helpers, but degrades gracefully if they are absent.
//
// The puzzle card is built ONCE and then mutated. It used to re-render the
// whole app with innerHTML on every guess, which meant a new clue never
// "arrived" — the card blinked and a longer list appeared, the input lost
// focus, and no animation was possible. Now each guess appends a clue, paints
// the attempt pips and adds a chip for what you tried.
(function () {
  const DAILY_URL = 'content/daily.json?v=1';
  const MAX_ATTEMPTS = 5;

  let entry = null;
  let attempts = [];     // [{ guess, correct }]
  let cluesShown = 1;
  let finished = false;
  let solved = false;

  function pad(n) { return String(n).padStart(2, '0'); }
  function isoOf(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }
  function todayISO() { return isoOf(new Date()); }
  function yesterdayISO() { const d = new Date(); d.setDate(d.getDate() - 1); return isoOf(d); }
  function dayIndex() { return Math.floor((new Date() - new Date(2026, 0, 1)) / 86400000); }
  function norm(s) { return String(s || '').trim().toLowerCase().replace(/[^a-z0-9]/g, ''); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function reduceMotion() {
    return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  function pickEntry(list) {
    const t = todayISO();
    const exact = list.find((e) => e.date === t);
    if (exact) return exact;
    const i = ((dayIndex() % list.length) + list.length) % list.length;
    return list[i];
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

  /**
   * Emoji grid — for the SHARE text only. In a WhatsApp message the squares are
   * exactly right (that is the Wordle convention people recognise); on our dark
   * page they rendered as ugly light-grey blocks, which is what the styled pips
   * below replace.
   */
  function resultGrid() {
    return attempts.map((a) => (a.correct ? '🟩' : '⬜')).join('');
  }

  // ── build once ──────────────────────────────────────────────────────────────

  function renderShell() {
    const app = document.getElementById('dailyApp');
    if (!app || !entry) return;
    const total = (entry.clues || []).length;

    app.innerHTML = `
      <article class="card featured">
        <div class="eyebrow">Today's Katha &middot; ${esc(entry.date || todayISO())}</div>
        <h2>${esc(entry.kathaTitle || 'A story for today')}</h2>
        <p>${esc(entry.teaser || '')}</p>
        <p id="dqLesson" class="dq-lesson" hidden><strong>Lesson:</strong> ${esc(entry.lesson || '')}</p>
      </article>

      <article class="card dq" style="margin-top:1rem">
        <div class="eyebrow">Daily Puzzle &middot; Guess the deity</div>
        <h3 id="dqStatus" class="dq-status">Clue 1 of ${total}</h3>

        <ol class="dq-clues" id="dqClues"></ol>

        <div class="dq-track">
          <div class="dq-pips" id="dqPips" aria-hidden="true"></div>
          <span class="dq-left" id="dqLeft">${MAX_ATTEMPTS} guesses</span>
        </div>

        <div class="dq-tried" id="dqTried"></div>

        <form id="dqForm" class="dq-form" autocomplete="off">
          <label class="dq-label" for="dqInput">Your guess</label>
          <div class="dq-row">
            <input id="dqInput" class="dq-input" type="text" autocomplete="off"
                   autocapitalize="words" spellcheck="false"
                   placeholder="A deity's name&hellip;" required>
            <button class="btn primary dq-go" type="submit">Guess</button>
          </div>
        </form>

        <p class="dq-msg" id="dqMsg" role="status" aria-live="polite"></p>

        <div class="dq-end" id="dqEnd" hidden></div>
      </article>
    `;

    document.getElementById('dqForm').addEventListener('submit', onGuess);
    addClue(0, true);
    paintPips();
  }

  // ── mutations ───────────────────────────────────────────────────────────────

  /** Append clue i, mark it as the newest, and dim the ones already read. */
  function addClue(i, first) {
    const host = document.getElementById('dqClues');
    const clue = (entry.clues || [])[i];
    if (!host || clue == null) return;

    Array.prototype.forEach.call(host.querySelectorAll('.dq-clue'), function (el) {
      el.classList.remove('is-new');
      el.classList.add('is-old');
    });

    const li = document.createElement('li');
    li.className = 'dq-clue is-new' + (first ? '' : ' is-entering');
    li.innerHTML =
      '<span class="dq-clue-n">Clue ' + (i + 1) + '</span>' +
      '<span class="dq-clue-text">' + esc(clue) + '</span>' +
      (first ? '' : '<span class="dq-clue-tag">new</span>');
    host.appendChild(li);

    if (!first && !reduceMotion()) {
      // let the browser paint the collapsed state, then animate to open
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { li.classList.remove('is-entering'); });
      });
    } else {
      li.classList.remove('is-entering');
    }

    const status = document.getElementById('dqStatus');
    if (status && !finished) {
      status.textContent = 'Clue ' + (i + 1) + ' of ' + (entry.clues || []).length;
    }
  }

  /** Five pips: what you have spent, and what is left. */
  function paintPips() {
    const host = document.getElementById('dqPips');
    if (!host) return;
    let html = '';
    for (let i = 0; i < MAX_ATTEMPTS; i++) {
      const a = attempts[i];
      const cls = !a ? 'dq-pip' : (a.correct ? 'dq-pip is-right' : 'dq-pip is-wrong');
      html += '<span class="' + cls + '"></span>';
    }
    host.innerHTML = html;

    const left = document.getElementById('dqLeft');
    if (left) {
      const remaining = MAX_ATTEMPTS - attempts.length;
      left.textContent = finished
        ? (solved ? 'Solved in ' + attempts.length + (attempts.length === 1 ? ' guess' : ' guesses') : 'Out of guesses')
        : remaining + (remaining === 1 ? ' guess left' : ' guesses left');
    }
  }

  /** Show what was already tried, so nobody repeats a guess. */
  function addTried(guess, correct) {
    const host = document.getElementById('dqTried');
    if (!host) return;
    const chip = document.createElement('span');
    chip.className = 'dq-chip' + (correct ? ' is-right' : '');
    chip.textContent = guess;
    host.appendChild(chip);
  }

  function say(msg, tone) {
    const el = document.getElementById('dqMsg');
    if (!el) return;
    el.textContent = msg;
    el.className = 'dq-msg' + (tone ? ' is-' + tone : '');
  }

  function shakeInput() {
    const input = document.getElementById('dqInput');
    if (!input) return;
    if (reduceMotion()) return;
    input.classList.remove('is-shake');
    void input.offsetWidth;      // restart the animation
    input.classList.add('is-shake');
    // Clear it again, or the red border lingers and the field looks permanently
    // in error while the next guess is being typed.
    const clear = function () { input.classList.remove('is-shake'); };
    input.addEventListener('animationend', clear, { once: true });
    input.addEventListener('input', clear, { once: true });
    setTimeout(clear, 700);
  }

  /** Self-contained canvas confetti, ported from kids-games.js. */
  function confettiBurst(count, duration) {
    if (reduceMotion()) return;
    const cv = document.createElement('canvas');
    cv.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:9999';
    cv.width = window.innerWidth; cv.height = window.innerHeight;
    document.body.appendChild(cv);
    const ctx = cv.getContext('2d');
    const colors = ['#E8B94F', '#E07B1A', '#F5A23C', '#6fcf97', '#F7EBD2'];
    const parts = [];
    for (let i = 0; i < count; i++) {
      parts.push({
        x: cv.width / 2 + (Math.random() - 0.5) * cv.width * 0.4,
        y: cv.height * 0.34 + (Math.random() - 0.5) * 50,
        vx: (Math.random() - 0.5) * 9, vy: Math.random() * -9 - 2,
        g: 0.22 + Math.random() * 0.12, s: 5 + Math.random() * 7,
        c: colors[i % colors.length], r: Math.random() * Math.PI, vr: (Math.random() - 0.5) * 0.32
      });
    }
    const start = performance.now();
    (function frame(t) {
      const el = t - start;
      ctx.clearRect(0, 0, cv.width, cv.height);
      parts.forEach(function (p) {
        p.vy += p.g; p.x += p.vx; p.y += p.vy; p.r += p.vr;
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r);
        ctx.fillStyle = p.c; ctx.fillRect(-p.s / 2, -p.s / 2, p.s, p.s * 0.6); ctx.restore();
      });
      if (el < duration) requestAnimationFrame(frame); else cv.remove();
    })(start);
  }

  // ── the ending ──────────────────────────────────────────────────────────────

  function finishUI(streak) {
    const answer = entry.answer || '';
    const deity = norm(entry.deity || answer);
    const known = ['rama', 'krishna', 'durga', 'ganesha', 'hanuman', 'shani', 'saraswati', 'narasimha'];
    const art = known.indexOf(deity) !== -1 ? 'Images/home/daily-' + deity + '.jpg' : '';

    const share = `Khatakshetra Daily — ${entry.date || todayISO()}\n` +
      `${solved ? `Guessed ${answer} in ${attempts.length}/${MAX_ATTEMPTS}` : `Stumped by ${answer}`} ${resultGrid()}\n` +
      `Streak: ${streak} — play at https://khatakshetra.com/daily`;

    const form = document.getElementById('dqForm');
    if (form) form.hidden = true;
    const tried = document.getElementById('dqTried');

    const status = document.getElementById('dqStatus');
    if (status) status.textContent = solved ? 'You got it.' : 'The answer was…';

    const lesson = document.getElementById('dqLesson');
    if (lesson) lesson.hidden = false;

    const end = document.getElementById('dqEnd');
    if (!end) return;
    end.hidden = false;
    end.innerHTML =
      '<div class="dq-reveal">' +
        (art ? '<div class="dq-art"><img src="' + art + '" alt="' + esc(answer) + '" ' +
               'onerror="this.parentNode.style.display=\'none\'"></div>' : '') +
        '<div class="dq-reveal-body">' +
          '<div class="dq-answer">' + esc(answer) + '</div>' +
          '<p class="dq-verdict">' + (solved
            ? 'Solved in ' + attempts.length + (attempts.length === 1 ? ' guess' : ' guesses') +
              ' &mdash; your streak is now ' + streak + '.'
            : 'Not this time &mdash; the clues pointed to ' + esc(answer) +
              '. Your streak is ' + streak + '; tomorrow is a fresh katha.') + '</p>' +
          '<div class="dq-streak"><span>&#128293; Streak ' + streak + '</span>' +
            '<span>' + (solved ? 'Solved' : 'Revealed') + '</span></div>' +
        '</div>' +
      '</div>' +
      '<div class="dq-actions">' +
        '<a class="btn primary" id="dqWa" target="_blank" rel="noopener">Share on WhatsApp</a>' +
        '<button class="btn" type="button" id="dqCopy">Copy result</button>' +
        '<a class="btn" href="games.html">More quizzes</a>' +
      '</div>' +
      '<textarea id="dqShareText" readonly aria-hidden="true" tabindex="-1" ' +
        'style="position:absolute;left:-9999px">' + esc(share) + '</textarea>';

    if (tried && attempts.length) tried.classList.add('is-done');
    paintPips();
    wireShare();
    if (solved) confettiBurst(90, 1500);
  }

  function wireShare() {
    const txt = document.getElementById('dqShareText');
    const wa = document.getElementById('dqWa');
    if (wa && txt) wa.href = `https://wa.me/?text=${encodeURIComponent(txt.value)}`;
    const copy = document.getElementById('dqCopy');
    if (copy && txt) {
      copy.addEventListener('click', function () {
        try { txt.select(); document.execCommand('copy'); } catch (e) {}
        if (navigator.clipboard) navigator.clipboard.writeText(txt.value).catch(function () {});
        copy.textContent = 'Copied!';
        setTimeout(function () { copy.textContent = 'Copy result'; }, 1500);
      });
    }
  }

  function finish() {
    finished = true;
    // Saving progress must never withhold the answer. If storage is blocked the
    // puzzle still resolves — it simply is not remembered.
    let streak = 0;
    try { streak = recordCompletion(); } catch (e) { streak = 0; }
    finishUI(streak);
    if (solved && entry.card && typeof revealTalapatraCard === 'function') {
      setTimeout(function () { revealTalapatraCard(entry.card); }, 500);
    }
    // The daily habit loop hands off to the 7-day journey here — this was the
    // missing doorway between /daily and /start.
    if (typeof khatakshetraOfferNextStep === 'function') {
      try {
        khatakshetraOfferNextStep({
          mount: document.getElementById('dailyApp'),
          context: 'daily',
          cta: 'daily_' + (solved ? 'solved' : 'played'),
          heading: solved ? 'Seven more like this, in order.' : 'Tomorrow is a fresh katha.',
          copy: solved
            ? 'The 7-day family journey takes one story a night — with a question to ask your children and a card to keep.'
            : 'Save your streak so it survives a closed tab, and we will send the next story.',
          button: 'Save my streak',
          actions: [
            { label: 'Start the 7-day journey', href: 'start.html', kxCta: 'after_daily_journey' },
            { label: 'Colour today’s deity', href: 'paint.html', kxCta: 'after_daily_colour' },
            { label: 'Free festival kits', href: 'kits.html', kxCta: 'after_daily_kits' }
          ]
        });
      } catch (e) {}
    }
    return streak;
  }

  // ── the guess ───────────────────────────────────────────────────────────────

  function onGuess(e) {
    e.preventDefault();
    if (finished) return;
    const input = document.getElementById('dqInput');
    const raw = (input ? input.value : '').trim();
    const guess = norm(raw);
    if (!guess) { shakeInput(); say('Type a name first.', 'warn'); return; }

    // A repeat costs nothing — punishing a forgetful guess just annoys people.
    if (attempts.some(function (a) { return norm(a.guess) === guess; })) {
      shakeInput();
      say('You have already tried that one.', 'warn');
      if (input) input.select();
      return;
    }

    const accept = [entry.answer].concat(entry.accept || []).map(norm);
    const correct = accept.indexOf(guess) !== -1;

    attempts.push({ guess: raw, correct: correct });
    addTried(raw, correct);
    paintPips();
    if (input) input.value = '';

    if (correct) {
      solved = true;
      say('Correct.', 'right');
      finish();
      return;
    }

    if (attempts.length >= MAX_ATTEMPTS) {
      solved = false;
      say('That was the last guess.', 'wrong');
      finish();
      return;
    }

    shakeInput();
    const remaining = MAX_ATTEMPTS - attempts.length;
    const hasMoreClues = cluesShown < (entry.clues || []).length;

    if (hasMoreClues) {
      addClue(cluesShown, false);
      cluesShown += 1;
      say('Not ' + raw + '. Here is another clue — ' + remaining +
          (remaining === 1 ? ' guess left.' : ' guesses left.'), 'wrong');
    } else {
      say('Not ' + raw + '. No clues left — ' + remaining +
          (remaining === 1 ? ' guess left.' : ' guesses left.'), 'wrong');
    }
    if (input) input.focus();
  }

  fetch(DAILY_URL)
    .then(function (r) { return r.json(); })
    .then(function (list) {
      if (!Array.isArray(list) || !list.length) return;
      entry = pickEntry(list);
      renderShell();
      // One of the strategy doc's ten events, previously never fired: we only
      // knew when someone FINISHED the daily, not when they started it.
      if (window.kxTrack && window.kxTrack.activityStarted) {
        window.kxTrack.activityStarted('daily_katha', entry.deity || entry.kathaTitle || '');
      }
    })
    .catch(function () {
      const app = document.getElementById('dailyApp');
      if (app) app.innerHTML = '<article class="card"><h3>Today’s puzzle is resting.</h3><p>Please check back soon.</p></article>';
    });
})();
