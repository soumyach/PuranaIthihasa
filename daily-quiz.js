// Daily Quiz — 5 questions drawn deterministically from the whole quiz pool by
// date, so everyone gets the same set each day. Reuses content/quizzes.json.
(function () {
  function el(id) { return document.getElementById(id); }
  function pad(n) { return String(n).padStart(2, '0'); }
  function todayISO() { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }
  function dayIndex() { return Math.floor((new Date() - new Date(2026, 0, 1)) / 86400000); }

  // mulberry32 seeded RNG → deterministic daily pick
  function rng(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function seededPick(pool, n, seed) {
    const idx = pool.map((_, i) => i);
    const r = rng(seed);
    for (let i = idx.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); const t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
    return idx.slice(0, n).map((i) => pool[i]);
  }

  const QN = 5;
  let questions = [], index = 0, score = 0, locked = false;
  const doneKey = 'khatakshetra.dailyquiz.' + todayISO();

  function renderQuestion() {
    const q = questions[index];
    locked = false;
    el('dqApp').innerHTML = `
      <article class="card featured">
        <div class="eyebrow">Daily Quiz &middot; ${todayISO()} &middot; Q${index + 1} of ${questions.length}</div>
        <div class="progress-track" style="height:8px;background:rgba(255,255,255,.08);border:1px solid rgba(232,185,79,.2);margin:.5rem 0 1rem"><div style="height:100%;width:${Math.round((index / questions.length) * 100)}%;background:linear-gradient(90deg,var(--gold,#e8b94f),var(--saffron,#e07b1a))"></div></div>
        <h2>${q.question}</h2>
        <div id="dqChoices"></div>
        <p id="dqExplain" style="display:none"></p>
      </article>`;
    const wrap = el('dqChoices');
    q.choices.forEach((choice) => {
      const b = document.createElement('button');
      b.className = 'btn'; b.type = 'button';
      b.style.cssText = 'width:100%;justify-content:flex-start;text-align:left;margin:.4rem 0';
      b.textContent = choice;
      b.addEventListener('click', () => choose(b, q, choice));
      wrap.appendChild(b);
    });
  }

  function choose(button, q, picked) {
    if (locked) return;
    locked = true;
    const correct = picked === q.answer;
    if (correct) {
      score += 1;
      if (typeof awardKhatakshetraProgress === 'function') { try { awardKhatakshetraProgress('daily_quiz_answer', { xp: 5, track: 'story_mastery' }); } catch (e) {} }
    }
    el('dqChoices').querySelectorAll('button').forEach((b) => {
      if (b.textContent === q.answer) b.style.borderColor = 'rgba(87,171,96,.9)';
      if (b === button && !correct) b.style.borderColor = 'rgba(192,79,58,.9)';
      b.disabled = true;
    });
    const ex = el('dqExplain'); ex.style.display = 'block'; ex.textContent = q.explanation || '';
    setTimeout(() => { index += 1; if (index < questions.length) renderQuestion(); else renderResult(); }, 1200);
  }

  function renderResult() {
    localStorage.setItem(doneKey, JSON.stringify({ score: score, total: questions.length, at: new Date().toISOString() }));
    if (typeof awardKhatakshetraProgress === 'function') { try { awardKhatakshetraProgress('daily_quiz_complete', { xp: 25, track: 'story_mastery', properties: { date: todayISO(), score: score } }); } catch (e) {} }
    const share = `Khatakshetra Daily Quiz ${todayISO()}: I scored ${score}/${questions.length}. Try it at https://khatakshetra.com/daily-quiz`;
    el('dqApp').innerHTML = `
      <article class="card featured" style="text-align:center">
        <div class="eyebrow">Daily Quiz complete</div>
        <h2 style="margin:.3rem 0">${score} / ${questions.length}</h2>
        <p>${score === questions.length ? 'Perfect round! ' : ''}Come back tomorrow for a fresh five.</p>
        <div class="journey-actions" style="justify-content:center;flex-wrap:wrap;gap:.5rem;margin-top:1rem">
          <a class="btn primary" id="dqShare" target="_blank" rel="noopener">Share on WhatsApp</a>
          <button class="btn" type="button" id="dqCopy">Copy result</button>
          <a class="btn" href="games.html">More quizzes</a>
        </div>
        <textarea id="dqShareText" readonly style="position:absolute;left:-9999px">${share}</textarea>
      </article>`;
    const wa = el('dqShare'); if (wa) wa.href = `https://wa.me/?text=${encodeURIComponent(share)}`;
    const copy = el('dqCopy');
    if (copy) copy.addEventListener('click', function () {
      const t = el('dqShareText'); t.select();
      try { document.execCommand('copy'); } catch (e) {}
      if (navigator.clipboard) navigator.clipboard.writeText(share).catch(function () {});
      copy.textContent = 'Copied!'; setTimeout(function () { copy.textContent = 'Copy result'; }, 1500);
    });
  }

  fetch('content/quizzes.json?v=20260518a')
    .then(function (r) { return r.json(); })
    .then(function (quizzes) {
      const pool = [];
      quizzes.forEach(function (q) { (q.questions || []).forEach(function (qq) { pool.push(qq); }); });
      if (!pool.length) return;
      questions = seededPick(pool, Math.min(QN, pool.length), dayIndex() + 1);
      renderQuestion();
    })
    .catch(function () { const a = el('dqApp'); if (a) a.innerHTML = '<article class="card"><h3>The daily quiz is resting.</h3></article>'; });
})();
