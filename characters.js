// キャラクターの絵データ(一覧は chars.js の window.PW_INDEX、絵は chars/<id>.json)を、描画用のピクセル格子とパレットに変換する。
// 体は「文字」の格子。文字: k=輪郭 e=目 小文字=色 大文字=その色の影。
(() => {
  const OUTLINE = '#2b2233';

  // 足場の角(ledge)は、よじ登りフレームの (LEDGE_COL, ledgeRow)。
  // 足場はそこから右下の領域にあるものとして描く(左向きは反転)。標準の粗さでの列。
  const LEDGE_COL = 18;

  const grid = (w, h) => Array.from({ length: h }, () => Array(w).fill('.'));

  // Scale2x (EPX) で解像度を 2 倍にして、斜めや角を滑らかにする
  function upscale(g) {
    const h = g.length;
    const w = g[0].length;
    const out = grid(w * 2, h * 2);
    const at = (x, y) => (x < 0 || y < 0 || x >= w || y >= h ? '.' : g[y][x]);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const P = g[y][x];
        const A = at(x, y - 1);
        const B = at(x + 1, y);
        const C = at(x - 1, y);
        const D = at(x, y + 1);
        out[2 * y][2 * x] = C === A && C !== D && A !== B ? A : P;
        out[2 * y][2 * x + 1] = A === B && A !== C && B !== D ? B : P;
        out[2 * y + 1][2 * x] = D === C && D !== B && C !== A ? C : P;
        out[2 * y + 1][2 * x + 1] = B === D && B !== A && D !== C ? D : P;
      }
    }
    return out;
  }

  // 色を明るく(f>1)/暗く(f<1)する
  function tint(hex, f) {
    const n = parseInt(hex.slice(1), 16);
    const ch = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) =>
      Math.round(f < 1 ? v * f : v + (255 - v) * (f - 1))
    );
    return '#' + ch.map((v) => v.toString(16).padStart(2, '0')).join('');
  }

  // ピクセル格子を canvas に描く。shade なら、シルエットの縁に沿って下・右を暗く、上・左を明るくする。
  function render(g, pal, dot, shade) {
    const h = g.length;
    const w = g[0].length;
    const c = document.createElement('canvas');
    c.width = Math.round(w * dot);
    c.height = Math.round(h * dot);
    const cx = c.getContext('2d');
    const at = (x, y) => (x < 0 || y < 0 || x >= w || y >= h ? '.' : g[y][x]);
    // (x,y) から (dx,dy) 方向に輪郭 k を抜けた先が透明なら、そこはシルエットの縁
    const edge = (x, y, dx, dy) => {
      let cxp = x + dx;
      let cyp = y + dy;
      if (at(cxp, cyp) !== 'k') return false;
      for (let i = 0; i < 4; i++) {
        cxp += dx;
        cyp += dy;
        const ch = at(cxp, cyp);
        if (ch === '.') return true;
        if (ch !== 'k') return false;
      }
      return false;
    };
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const ch = g[y][x];
        let col = pal[ch];
        if (!col) continue;
        if (shade && ch !== 'k') {
          if (edge(x, y, 0, 1) || edge(x, y, 1, 0)) col = tint(col, 0.82);
          else if (edge(x, y, 0, -1) || edge(x, y, -1, 0)) col = tint(col, 1.18);
        }
        cx.fillStyle = col;
        const x0 = Math.round(x * dot);
        const y0 = Math.round(y * dot);
        cx.fillRect(x0, y0, Math.round((x + 1) * dot) - x0, Math.round((y + 1) * dot) - y0);
      }
    }
    return c;
  }

  // 行の連長圧縮(文字 + 連続数)を展開する
  function decodeRow(enc) {
    const out = [];
    const re = /(.)(\d*)/g;
    let m;
    while ((m = re.exec(enc))) for (let i = 0, n = m[2] ? Number(m[2]) : 1; i < n; i++) out.push(m[1]);
    return out;
  }

  // 絵データは chars/<id>.json に 1 体ずつ。使う 1 体だけを load() で読み込んで覚えておく
  // (全部を全ページに読み込むと重いため)
  const INDEX = window.PW_INDEX;
  const RAW = {};
  const cache = {};
  const loading = {};
  function find(id) {
    const key = RAW[id] ? id : Object.keys(RAW)[0];
    if (!key) throw new Error('Pixel Walker: 絵データが読み込まれていません: ' + id);
    return cache[key] || (cache[key] = JSON.parse(RAW[key]));
  }

  // 拡張機能のページ(ポップアップ)は自分で読める。Webページに入る content script は、
  // background.js に読んでもらう(拡張機能の中のファイルを読むだけで、外部とは通信しない)
  function fetchText(id) {
    const url = chrome.runtime.getURL(`chars/${id}.json`);
    if (location.protocol === 'chrome-extension:') return fetch(url).then((r) => r.text());
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ type: 'pw-char', id }, (res) => {
        if (chrome.runtime.lastError || !res || !res.text) reject(new Error('load failed: ' + id));
        else resolve(res.text);
      });
    });
  }

  function load(id) {
    if (RAW[id]) return Promise.resolve(id);
    if (!INDEX.some(([cid]) => cid === id)) return Promise.reject(new Error('unknown character: ' + id));
    return (loading[id] ||= fetchText(id).then(
      (text) => {
        RAW[id] = text;
        return id;
      },
      (e) => {
        delete loading[id];
        throw e;
      }
    ));
  }

  function palette(id) {
    const p = { k: OUTLINE, e: '#0f0b14', ...find(id).palette };
    const out = { ...p };
    for (const [k, v] of Object.entries(p)) {
      const K = k.toUpperCase();
      if (k !== 'k' && k !== K && !p[K]) out[K] = tint(v, 0.8); // 大文字 = 影(指定がなければ)
    }
    for (const k of ['t', 'l', 'a']) {
      if (!p[k]) {
        out[k] = out.y;
        out[k.toUpperCase()] = out.Y;
      }
    }
    return out;
  }

  // 1 セルの大きさ(標準の粗さのドットに対する比)
  const unit = (id) => find(id).unit || 1;

  // 泳ぐキャラクター(魚・海の生き物・カエル)なら { frames, speed }。地面を歩かず、画面を自由に泳ぐ
  const swim = (id) => find(id).swim || null;

  // fine: 手で陰影まで描いた細かい絵。補間(2 倍化)や縁取りの自動陰影はかけず、そのまま表示する
  const fine = (id) => !!find(id).fine;

  const FRAME_NAMES = ['idle', 'walk1', 'walk2', 'jump', 'fall', 'sit', 'sleep', 'hang1', 'hang2', 'pull1', 'pull2', 'pull3'];

  // 全フレームのピクセル格子 { name: { g, ax, ledgeRow? } }。res: 1 = そのまま / 2 = 2 倍の解像度に補間
  // (飛ぶ・泳ぐキャラクターなど、絵の無いフレームは待機の絵で代用する)
  function grids(id, res = 1) {
    const out = {};
    const frames = find(id).frames;
    for (const name of new Set([...FRAME_NAMES, ...Object.keys(frames)])) {
      const f = frames[name] || frames.idle;
      out[name] = { g: f.rows.map(decodeRow), ax: f.ax, ledgeRow: f.ledgeRow };
    }
    if (res === 2) {
      for (const f of Object.values(out)) {
        f.g = upscale(f.g);
        f.ax *= 2;
        if (f.ledgeRow) f.ledgeRow *= 2;
      }
    }
    return out;
  }

  // 表示言語に翻訳されたキャラクター名があればそれを使う(無ければchars.jsの日本語名のまま)
  function localizedLabel(id, fallback) {
    try {
      return (typeof chrome !== 'undefined' && chrome.i18n && chrome.i18n.getMessage(`char_${id}`)) || fallback;
    } catch {
      return fallback;
    }
  }

  window.PW = {
    list: INDEX.map(([id, label, genre]) => ({ id, label: localizedLabel(id, label), genre: genre || 'animals' })),
    genres: window.PW_GENRES || ['animals'],
    load,
    palette,
    grids,
    unit,
    swim,
    fine,
    render,
    LEDGE_COL,
  };
})();
