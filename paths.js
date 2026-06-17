// Completion Rings — "Your Paths". Shows progress toward a few defined paths,
// read from the local (and, once signed in, synced) profile + localStorage.
// The psychological driver is closure: people want to finish visible sets.
(function () {
  function profile() {
    try { return (typeof getKhatakshetraProfile === 'function') ? getKhatakshetraProfile() : JSON.parse(localStorage.getItem('khatakshetra_profile') || '{}'); }
    catch (e) { return {}; }
  }

  function quizCount() {
    let n = 0;
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.indexOf('khatakshetra.quiz.') === 0) n += 1;
    }
    return n;
  }

  function journeyNodes(key) {
    try {
      const s = JSON.parse(localStorage.getItem(key) || '{}');
      return (s.completed || []).length;
    } catch (e) { return 0; }
  }

  function progressFor(check) {
    const p = profile();
    if (check.type === 'journeyNodes') return journeyNodes(check.key);
    if (check.type === 'quizCount') return quizCount();
    if (check.type === 'cardCount') return (p.cards || []).length;
    if (check.type === 'streak') return (p.daily && p.daily.streak) || 0;
    return 0;
  }

  function ring(done, total) {
    const pct = Math.max(0, Math.min(1, total ? done / total : 0));
    const R = 26, C = 2 * Math.PI * R;
    const off = C * (1 - pct);
    const colour = pct >= 1 ? '#57ab60' : 'var(--gold, #e8b94f)';
    return `
      <svg width="68" height="68" viewBox="0 0 68 68" aria-hidden="true" style="flex:0 0 auto">
        <circle cx="34" cy="34" r="${R}" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="6"></circle>
        <circle cx="34" cy="34" r="${R}" fill="none" stroke="${colour}" stroke-width="6" stroke-linecap="round"
          stroke-dasharray="${C.toFixed(1)}" stroke-dashoffset="${off.toFixed(1)}" transform="rotate(-90 34 34)"></circle>
        <text x="34" y="39" text-anchor="middle" font-size="15" fill="#f4ead9" font-family="Cinzel, serif">${done}/${total}</text>
      </svg>`;
  }

  function render(paths) {
    const grid = document.getElementById('pathsGrid');
    if (!grid) return;
    grid.innerHTML = paths.map(function (path) {
      const done = progressFor(path.check);
      const total = path.check.total;
      const complete = done >= total;
      return `
        <article class="card ${complete ? 'featured' : ''}">
          <div style="display:flex;align-items:center;gap:1rem">
            ${ring(Math.min(done, total), total)}
            <div style="min-width:0">
              <div class="eyebrow">${path.emoji} ${complete ? 'Complete' : 'In progress'}</div>
              <h3 style="margin:.15rem 0">${path.title}</h3>
              <p style="margin:0">${path.subtitle}</p>
            </div>
          </div>
          <p style="margin:.7rem 0 0"><strong>${complete ? 'Earned:' : 'Unlocks:'}</strong> ${path.reward}</p>
          <div class="journey-actions" style="margin-top:.6rem">
            <a class="btn ${complete ? '' : 'primary'}" href="${path.cta.href}">${complete ? 'Revisit' : path.cta.label}</a>
          </div>
        </article>`;
    }).join('');
  }

  if (typeof renderKhatakshetraProgress === 'function') {
    try { renderKhatakshetraProgress('progressPanel'); } catch (e) {}
  }

  fetch('content/paths.json?v=1')
    .then(function (res) { return res.json(); })
    .then(render)
    .catch(function () {
      const grid = document.getElementById('pathsGrid');
      if (grid) grid.innerHTML = '<article class="card"><h3>Paths are loading soon.</h3></article>';
    });
})();
