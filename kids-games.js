// Kids Games hub — image-driven mini-games with categories + difficulty levels.
// Card art comes from content/kids-games.json (assets are embedded data URIs).
// Completion awards a little XP via site.js (awardKhatakshetraProgress).
(function () {
  let DATA = null;
  function app() { return document.getElementById('kidsApp'); }

  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }
  function img(id) { return (DATA.assets && DATA.assets[id]) || ''; }
  function award(game, props) {
    if (typeof awardKhatakshetraProgress === 'function') {
      try { awardKhatakshetraProgress('kids_game_complete', { xp: 15, track: 'creative_practice', properties: Object.assign({ game: game }, props || {}) }); } catch (e) {}
    }
  }
  function bar(label, handler) {
    const b = document.createElement('button');
    b.className = 'btn kg-back'; b.type = 'button'; b.textContent = label || '‹ Back';
    b.addEventListener('click', handler);
    return b;
  }
  function head(backLabel, backFn, title, subtitle) {
    const wrap = document.createElement('div');
    wrap.appendChild(bar(backLabel, backFn));
    const h = document.createElement('h2'); h.className = 'kg-title'; h.textContent = title; wrap.appendChild(h);
    if (subtitle) { const p = document.createElement('p'); p.className = 'kg-sub'; p.textContent = subtitle; wrap.appendChild(p); }
    return wrap;
  }
  function chooser(options) {
    const grid = document.createElement('div');
    grid.className = 'kg-choose';
    options.forEach(function (o) {
      const c = document.createElement('button');
      c.type = 'button';
      c.className = 'kg-opt' + (o.locked ? ' is-locked' : '');
      let inner = '';
      if (o.thumb) inner += '<span class="kg-opt-thumb" style="background-image:url(' + o.thumb + ')"></span>';
      inner += '<span class="kg-opt-body"><span class="kg-opt-name">' + o.name + '</span>';
      if (o.sub) inner += '<span class="kg-opt-sub">' + o.sub + '</span>';
      inner += '</span>';
      c.innerHTML = inner;
      if (o.locked) { c.disabled = true; }
      else { c.addEventListener('click', o.onClick); }
      grid.appendChild(c);
    });
    return grid;
  }
  function msg(text) {
    const p = document.createElement('p'); p.className = 'kg-msg'; p.id = 'kgMsg'; p.textContent = text || ''; return p;
  }
  function setMsg(t) { const m = document.getElementById('kgMsg'); if (m) m.textContent = t; }
  function clear() { const a = app(); a.innerHTML = ''; return a; }
  function actionsBar() { const d = document.createElement('div'); d.className = 'kg-actions'; d.id = 'kgActions'; return d; }
  function clearActions() { const h = document.getElementById('kgActions'); if (h) h.innerHTML = ''; }
  function showActions(actions) {
    const host = document.getElementById('kgActions');
    if (!host) return;
    host.innerHTML = '';
    actions.forEach(function (a) {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'btn' + (a.primary ? ' primary' : '');
      b.textContent = a.label; b.addEventListener('click', a.onClick);
      host.appendChild(b);
    });
    try { host.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (e) {}
  }

  // ───────────────────────── Menu ─────────────────────────
  function renderMenu() {
    const a = clear();
    const grid = document.createElement('div'); grid.className = 'kg-menu';
    const games = [
      { id: 'memory', tag: '🧠 Pairs', name: 'Memory Match', desc: 'Flip cards to find matching pairs. Choose a theme and a level.', go: renderMemoryThemes },
      { id: 'vahana', tag: '🦅 Match', name: 'Match the Vahana', desc: 'Pair each deity with the mount (vahana) they ride.', go: renderVahanaLevels },
      { id: 'sequence', tag: '🔢 Order', name: 'Story Order', desc: 'Put the events of an epic in the order they happen.', go: renderSequenceCats },
      { id: 'jigsaw', tag: '🧩 Puzzle', name: 'Sliding Picture', desc: 'Slide the tiles to complete a picture.', go: renderJigsawChoices }
    ];
    games.forEach(function (g) {
      const c = document.createElement('article'); c.className = 'card kg-gamecard';
      c.innerHTML = '<div class="eyebrow">' + g.tag + '</div><h3>' + g.name + '</h3><p>' + g.desc + '</p>';
      const b = document.createElement('button'); b.className = 'btn primary'; b.type = 'button'; b.textContent = 'Play';
      b.addEventListener('click', g.go); c.appendChild(b); grid.appendChild(c);
    });
    a.appendChild(grid);
  }

  // ─────────────────── Memory: themes → levels → play ───────────────────
  function renderMemoryThemes() {
    const a = clear();
    a.appendChild(head('‹ All games', renderMenu, DATA.memory.title, 'Pick a theme.'));
    a.appendChild(chooser(DATA.memory.themes.map(function (th) {
      const sample = th.mode === 'related' ? (th.pairs[0] && th.pairs[0].a.id) : (th.cards[0] && th.cards[0].id);
      return { name: th.name, sub: th.tagline || '', thumb: img(sample), onClick: function () { renderMemoryLevels(th); } };
    })));
  }
  function renderMemoryLevels(theme) {
    const a = clear();
    a.appendChild(head('‹ Themes', renderMemoryThemes, theme.name, 'Pick a level.'));
    a.appendChild(chooser(theme.levels.map(function (lv) {
      return { name: lv.name, sub: lv.pairs + ' pairs · ' + (lv.pairs * 2) + ' cards', onClick: function () { playMemory(theme, lv); } };
    })));
  }
  function playMemory(theme, level) {
    const a = clear();
    a.appendChild(head('‹ Levels', function () { renderMemoryLevels(theme); }, theme.name + ' — ' + level.name));
    a.appendChild(msg('Find all the pairs.'));
    const moves = document.createElement('p'); moves.className = 'kg-stat'; moves.id = 'kgMoves'; moves.textContent = 'Moves: 0';
    a.appendChild(moves);

    let units = [];
    if (theme.mode === 'related') {
      shuffle(theme.pairs).slice(0, level.pairs).forEach(function (p, i) {
        units.push({ key: 'k' + i, id: p.a.id, label: p.a.label });
        units.push({ key: 'k' + i, id: p.b.id, label: p.b.label });
      });
    } else {
      shuffle(theme.cards).slice(0, level.pairs).forEach(function (card, i) {
        units.push({ key: 'k' + i, id: card.id, label: card.label });
        units.push({ key: 'k' + i, id: card.id, label: card.label });
      });
    }
    const deck = shuffle(units);
    const cols = level.pairs <= 3 ? 3 : (level.pairs <= 8 ? 4 : 5);
    const grid = document.createElement('div'); grid.className = 'kg-grid';
    grid.style.gridTemplateColumns = 'repeat(' + cols + ', 1fr)';
    a.appendChild(grid);
    a.appendChild(actionsBar());

    let first = null, lock = false, matched = 0, moves2 = 0;
    deck.forEach(function (unit) {
      const c = document.createElement('button');
      c.type = 'button'; c.className = 'kg-card';
      c.innerHTML = '<span class="kg-back">ॐ</span>' +
        '<span class="kg-face"><img src="' + img(unit.id) + '" alt="' + unit.label + '" loading="lazy"><span class="kg-cap">' + unit.label + '</span></span>';
      c.addEventListener('click', function () { flip(c, unit); });
      grid.appendChild(c);
    });
    function flip(c, unit) {
      if (lock || c.classList.contains('is-up') || c.classList.contains('is-done')) return;
      c.classList.add('is-up');
      if (!first) { first = { c: c, unit: unit }; return; }
      moves2++; document.getElementById('kgMoves').textContent = 'Moves: ' + moves2;
      if (first.unit.key === unit.key && first.c !== c) {
        first.c.classList.add('is-done'); c.classList.add('is-done');
        first = null; matched++;
        if (matched === level.pairs) {
          setMsg('You matched them all in ' + moves2 + ' moves! 🎉');
          award('memory', { theme: theme.id, level: level.name, moves: moves2 });
          const li = theme.levels.indexOf(level);
          const acts = [{ label: '↻ Play again', onClick: function () { playMemory(theme, level); } }];
          if (li > -1 && li < theme.levels.length - 1) acts.push({ label: 'Next level →', primary: true, onClick: function () { playMemory(theme, theme.levels[li + 1]); } });
          else acts.push({ label: 'Try another theme →', primary: true, onClick: renderMemoryThemes });
          showActions(acts);
        }
      } else {
        lock = true; const f = first; first = null;
        setTimeout(function () { f.c.classList.remove('is-up'); c.classList.remove('is-up'); lock = false; }, 850);
      }
    }
  }

  // ─────────────────── Match the Vahana (image, leveled) ───────────────────
  function renderVahanaLevels() {
    const a = clear();
    a.appendChild(head('‹ All games', renderMenu, DATA.vahana.title, 'Pick a level.'));
    a.appendChild(chooser(DATA.vahana.levels.map(function (lv) {
      return { name: lv.name, sub: lv.pairs + ' deities to match', onClick: function () { playVahana(lv); } };
    })));
  }
  function playVahana(level) {
    const a = clear();
    a.appendChild(head('‹ Levels', renderVahanaLevels, DATA.vahana.title + ' — ' + level.name));
    a.appendChild(msg('Tap a deity, then tap the vahana they ride.'));
    const pairs = shuffle(DATA.vahana.pairs).slice(0, level.pairs);
    pairs.forEach(function (p, i) { p._k = 'p' + i; });
    const cols = document.createElement('div'); cols.className = 'kg-cols';
    const dCol = document.createElement('div'); dCol.className = 'kg-col';
    const vCol = document.createElement('div'); vCol.className = 'kg-col';
    cols.appendChild(dCol); cols.appendChild(vCol); a.appendChild(cols);
    a.appendChild(actionsBar());

    function tile(item, key, col) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'kg-tile';
      b.dataset.key = key;
      b.innerHTML = '<img src="' + img(item.id) + '" alt="' + item.label + '" loading="lazy"><span class="kg-cap">' + item.label + '</span>';
      col.appendChild(b); return b;
    }
    let selected = null, matched = 0;
    shuffle(pairs).forEach(function (p) {
      const b = tile(p.deity, p._k, dCol);
      b.addEventListener('click', function () {
        if (b.classList.contains('is-done')) return;
        if (selected) selected.classList.remove('is-sel');
        selected = b; b.classList.add('is-sel');
      });
    });
    shuffle(pairs).forEach(function (p) {
      const b = tile(p.vahana, p._k, vCol);
      b.addEventListener('click', function () {
        if (b.classList.contains('is-done') || !selected) return;
        if (selected.dataset.key === b.dataset.key) {
          b.classList.add('is-done'); selected.classList.add('is-done');
          b.classList.remove('is-sel'); selected.classList.remove('is-sel');
          selected = null; matched++;
          if (matched === pairs.length) {
            setMsg('Perfect match! 🎉'); award('vahana', { level: level.name });
            const li = DATA.vahana.levels.indexOf(level);
            const acts = [{ label: '↻ Play again', onClick: function () { playVahana(level); } }];
            if (li > -1 && li < DATA.vahana.levels.length - 1) acts.push({ label: 'Next level →', primary: true, onClick: function () { playVahana(DATA.vahana.levels[li + 1]); } });
            else acts.push({ label: 'More games →', primary: true, onClick: renderMenu });
            showActions(acts);
          } else { setMsg('Yes! ' + matched + ' of ' + pairs.length + ' matched.'); }
        } else { setMsg('Not their vahana — try again.'); }
      });
    });
  }

  // ─────────────────── Story Order: category → level → play ───────────────────
  function renderSequenceCats() {
    const a = clear();
    a.appendChild(head('‹ All games', renderMenu, DATA.sequence.title, 'Pick an epic.'));
    a.appendChild(chooser(DATA.sequence.categories.map(function (cat) {
      return {
        name: cat.name + (cat.locked ? '  🔒' : ''),
        sub: cat.locked ? (cat.note || 'Coming soon') : (cat.items.length + ' scenes'),
        thumb: cat.items ? img(cat.items[0].id) : '',
        locked: !!cat.locked,
        onClick: function () { renderSequenceLevels(cat); }
      };
    })));
  }
  function renderSequenceLevels(cat) {
    const a = clear();
    a.appendChild(head('‹ Epics', renderSequenceCats, cat.name, 'Pick a level.'));
    a.appendChild(chooser(cat.levels.map(function (lv) {
      return { name: lv.name, sub: lv.count + ' scenes to order', onClick: function () { playSequence(cat, lv); } };
    })));
  }
  function playSequence(cat, level) {
    const a = clear();
    a.appendChild(head('‹ Levels', function () { renderSequenceLevels(cat); }, cat.name + ' — ' + level.name));
    a.appendChild(msg('Tap the scenes in the order they happen.'));
    const correct = cat.items.slice(0, level.count);
    const pool = shuffle(correct);
    let answer = [];
    const ansRow = document.createElement('div'); ansRow.className = 'kg-seq-answer'; ansRow.id = 'kgAns';
    const choices = document.createElement('div'); choices.className = 'kg-seq-choices'; choices.id = 'kgChoices';
    const reset = document.createElement('button'); reset.className = 'btn kg-reset'; reset.type = 'button'; reset.textContent = 'Reset';
    a.appendChild(ansRow); a.appendChild(choices); a.appendChild(reset); a.appendChild(actionsBar());

    function tileFor(item, n) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'kg-scene';
      b.innerHTML = (n ? '<span class="kg-ord">' + n + '</span>' : '') +
        '<img src="' + img(item.id) + '" alt="' + item.label + '" loading="lazy"><span class="kg-cap">' + item.label + '</span>';
      return b;
    }
    function render() {
      clearActions();
      choices.innerHTML = '';
      pool.forEach(function (item) {
        if (answer.indexOf(item) !== -1) return;
        const b = tileFor(item, 0);
        b.addEventListener('click', function () { answer.push(item); render(); });
        choices.appendChild(b);
      });
      ansRow.innerHTML = '';
      answer.forEach(function (item, i) {
        const b = tileFor(item, i + 1);
        b.addEventListener('click', function () { answer.splice(i, 1); render(); });
        ansRow.appendChild(b);
      });
      if (answer.length === correct.length) {
        const ok = answer.every(function (it, i) { return it === correct[i]; });
        if (ok) {
          setMsg('Correct order! 🎉'); award('sequence', { category: cat.id, level: level.name });
          const li = cat.levels.indexOf(level);
          const acts = [{ label: '↻ Play again', onClick: function () { playSequence(cat, level); } }];
          if (li > -1 && li < cat.levels.length - 1) acts.push({ label: 'Next level →', primary: true, onClick: function () { playSequence(cat, cat.levels[li + 1]); } });
          else acts.push({ label: 'Try another epic →', primary: true, onClick: renderSequenceCats });
          showActions(acts);
        } else { setMsg('Not quite — tap a placed scene to remove it, or Reset.'); }
      } else { setMsg('Tap the scenes in the order they happen.'); }
    }
    reset.addEventListener('click', function () { answer = []; render(); });
    render();
  }

  // ─────────────────── Sliding Picture (image picker + size) ───────────────────
  function renderJigsawChoices() {
    const a = clear();
    a.appendChild(head('‹ All games', renderMenu, DATA.jigsaw.title, 'Pick a picture and a size.'));
    let pick = DATA.jigsaw.choices[0];
    const picGrid = chooser(DATA.jigsaw.choices.map(function (ch) {
      return { name: ch.label, thumb: img(ch.id), onClick: function () { pick = ch; highlight(); } };
    }));
    a.appendChild(picGrid);
    function highlight() {
      const opts = picGrid.querySelectorAll('.kg-opt');
      DATA.jigsaw.choices.forEach(function (ch, i) { opts[i].classList.toggle('is-sel', ch === pick); });
    }
    highlight();
    const sizeRow = document.createElement('div'); sizeRow.className = 'kg-sizes';
    DATA.jigsaw.sizes.forEach(function (s) {
      const b = document.createElement('button'); b.className = 'btn primary'; b.type = 'button'; b.textContent = s.name;
      b.addEventListener('click', function () { playJigsaw(pick, s.size); });
      sizeRow.appendChild(b);
    });
    a.appendChild(sizeRow);
  }
  function playJigsaw(choice, size) {
    const a = clear();
    a.appendChild(head('‹ Pictures', renderJigsawChoices, DATA.jigsaw.title + ' — ' + choice.label));
    a.appendChild(msg('Slide tiles into the empty space to complete the picture.'));
    const image = img(choice.id);
    const n = size * size, blankVal = n - 1;
    let tiles = [], blank = n - 1;
    for (let i = 0; i < n; i++) tiles.push(i);
    function neighbors(b) {
      const r = Math.floor(b / size), c = b % size, res = [];
      if (r > 0) res.push(b - size);
      if (r < size - 1) res.push(b + size);
      if (c > 0) res.push(b - 1);
      if (c < size - 1) res.push(b + 1);
      return res;
    }
    for (let k = 0; k < 300; k++) {
      const nb = neighbors(blank); const t = nb[Math.floor(Math.random() * nb.length)];
      const tmp = tiles[blank]; tiles[blank] = tiles[t]; tiles[t] = tmp; blank = t;
    }
    const grid = document.createElement('div'); grid.className = 'kg-jig';
    grid.style.gridTemplateColumns = 'repeat(' + size + ', 1fr)';
    a.appendChild(grid);
    a.appendChild(actionsBar());
    function draw() {
      grid.innerHTML = '';
      tiles.forEach(function (val, pos) {
        const cell = document.createElement('button'); cell.type = 'button'; cell.className = 'kg-jigcell';
        if (val === blankVal) { cell.style.visibility = 'hidden'; }
        else {
          const r = Math.floor(val / size), c = val % size;
          cell.style.backgroundImage = 'url("' + image + '")';
          cell.style.backgroundSize = (size * 100) + '% ' + (size * 100) + '%';
          cell.style.backgroundPosition = (c * 100 / (size - 1)) + '% ' + (r * 100 / (size - 1)) + '%';
        }
        cell.addEventListener('click', function () { tryMove(pos); });
        grid.appendChild(cell);
      });
    }
    function tryMove(pos) {
      if (neighbors(blank).indexOf(pos) === -1) return;
      const tmp = tiles[blank]; tiles[blank] = tiles[pos]; tiles[pos] = tmp; blank = pos;
      draw();
      if (tiles.every(function (v, i) { return v === i; })) {
        setMsg('You solved it! 🎉'); award('jigsaw', { picture: choice.id, size: size });
        const acts = [{ label: '↻ Shuffle again', onClick: function () { playJigsaw(choice, size); } }];
        if (size < 4) acts.push({ label: 'Try 4 × 4 →', primary: true, onClick: function () { playJigsaw(choice, 4); } });
        else acts.push({ label: 'New picture →', primary: true, onClick: renderJigsawChoices });
        showActions(acts);
      }
    }
    draw();
  }

  fetch('content/kids-games.json?v=2')
    .then(function (r) { return r.json(); })
    .then(function (d) { DATA = d; renderMenu(); })
    .catch(function () { const a = app(); if (a) a.innerHTML = '<article class="card"><h3>Games are loading soon.</h3></article>'; });
})();
