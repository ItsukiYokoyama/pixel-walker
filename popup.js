const DEFAULTS = { enabled: true, scale: 4, character: 'adventurer', detail: 2, updateCheck: true, control: false };
const $ = (id) => document.getElementById(id);
const t = (key, subs) => chrome.i18n.getMessage(key, subs) || key;

// 静的な文言は読み込み時に一度だけ埋め込む(i18nメッセージはHTMLの属性では展開されないため)
document.title = t('extName');
$('app-title').textContent = t('extName');
$('enabled-label').textContent = t('enabledLabel');
$('size-label').textContent = t('sizeLabel');
$('size-small').textContent = t('sizeSmall');
$('size-medium').textContent = t('sizeMedium');
$('size-large').textContent = t('sizeLarge');
$('list').setAttribute('aria-label', t('characterGroupLabel'));
// 要望・お問い合わせは、表示言語のサイトのページを新しいタブで開くだけ(拡張機能からは何も送らない)
$('contact').textContent = t('contactLabel');
$('contact').href = `${t('contactUrl')}?product=pixel-walker`; // サイト側で「対象の拡張機能」として表示・記録される
$('update-check-label').textContent = t('updateCheckLabel');
$('control-label').textContent = t('controlLabel');
// キーの説明。[[...]] の中をキーの見た目(kbd)にする
for (const [i, part] of t('controlHelp').split(/\[\[(.+?)\]\]/).entries()) {
  if (i % 2) {
    const k = document.createElement('kbd');
    k.textContent = part;
    $('control-help').append(k);
  } else {
    $('control-help').append(part);
  }
}
$('update-badge').setAttribute('aria-label', t('updateBadgeLabel'));

// 設定を保存し、開いているタブにもすぐ反映する(選んだ瞬間に切り替わる)
function setSettings(changes) {
  chrome.storage.sync.set(changes);
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) return;
    chrome.tabs.sendMessage(tabs[0].id, { type: 'pw-set', changes }, () => void chrome.runtime.lastError);
  });
}

// 一覧の 1 枚ぶん(サムネイル + ラジオボタン + 名前)。サムネイルは、そのジャンルのタブを開いたときに描く
function card(id, label) {
  const el = document.createElement('label');
  el.className = 'card';
  el.title = label;

  const radio = document.createElement('input');
  radio.type = 'radio';
  radio.name = 'character';
  radio.value = id;
  radio.addEventListener('change', () => setSettings({ character: id }));

  const thumb = document.createElement('canvas');
  thumb.width = thumb.height = 1;

  const name = document.createElement('span');
  name.textContent = label;

  el.append(radio, thumb, name);
  return el;
}

// 待機のポーズを、絵のままの大きさで描く(表示側で拡大)
function drawThumb(id, el) {
  if (el.dataset.drawn) return;
  el.dataset.drawn = '1';
  PW.load(id)
    .then(() => {
      const sprite = PW.render(PW.grids(id, 1).idle.g, PW.palette(id), 1, false);
      const thumb = el.querySelector('canvas');
      thumb.width = sprite.width;
      thumb.height = sprite.height;
      thumb.getContext('2d').drawImage(sprite, 0, 0);
    })
    .catch(() => delete el.dataset.drawn);
}

const cards = new Map(); // id -> { el, genre }
for (const { id, label, genre } of PW.list) {
  const el = card(id, label);
  cards.set(id, { el, genre });
  $('list').appendChild(el);
}

// ジャンルのタブ
const tabs = new Map();
function showGenre(genre) {
  for (const [g, b] of tabs) b.setAttribute('aria-selected', String(g === genre));
  for (const [id, c] of cards) {
    c.el.hidden = c.genre !== genre;
    if (!c.el.hidden) drawThumb(id, c.el);
  }
  $('list').scrollTop = 0;
}
for (const genre of PW.genres) {
  if (![...cards.values()].some((c) => c.genre === genre)) continue;
  const b = document.createElement('button');
  b.type = 'button';
  b.setAttribute('role', 'tab');
  b.textContent = t(`genre_${genre}`);
  b.addEventListener('click', () => showGenre(genre));
  tabs.set(genre, b);
  $('tabs').appendChild(b);
}

chrome.storage.sync.get(DEFAULTS, (v) => {
  $('enabled').checked = v.enabled;
  $('scale').value = String(v.scale);
  const selected = cards.has(v.character) ? v.character : DEFAULTS.character;
  const { el, genre } = cards.get(selected);
  el.querySelector('input').checked = true;
  showGenre(genre); // 選択中のキャラクターのジャンルを開いて、見える位置へ
  el.scrollIntoView({ block: 'nearest' });
  $('control').checked = v.control;
  $('control-help').hidden = !v.control;
  $('update-check').checked = v.updateCheck;
  showUpdate(v.updateCheck);
});

$('enabled').addEventListener('change', (e) => setSettings({ enabled: e.target.checked }));
$('control').addEventListener('change', (e) => {
  setSettings({ control: e.target.checked });
  $('control-help').hidden = !e.target.checked;
});
$('update-check').addEventListener('change', (e) => {
  chrome.storage.sync.set({ updateCheck: e.target.checked });
  showUpdate(e.target.checked);
});

// ---------- 新しいバージョンのお知らせ ----------
// 「新しいバージョンがリリースされています。こちらから…」の「こちら」を、表示言語のリリースノートのページへのリンクにする
function renderUpdateBubble(latest) {
  const MARK = '\u0001';
  const [before, after = ''] = t('updateAvailable', MARK).split(MARK);
  const link = document.createElement('a');
  link.href = t('releasesUrl');
  link.target = '_blank';
  link.rel = 'noopener';
  link.textContent = t('updateLink');
  const versions = document.createElement('span');
  versions.id = 'update-versions';
  versions.textContent = t('updateVersions', [chrome.runtime.getManifest().version, latest]);
  $('update-bubble').replaceChildren(before, link, after, versions);
}

let updateSeq = 0;
async function showUpdate(enabled) {
  const seq = ++updateSeq;
  $('update').hidden = true;
  if (!enabled) return;
  const latest = await PWUpdate.check();
  if (seq !== updateSeq || !latest) return;
  renderUpdateBubble(latest);
  $('update').hidden = false;
}
// クリックでも開閉できるようにする(マウスを乗せる操作ができない場合のため)
$('update-badge').addEventListener('click', () => $('update').classList.toggle('open'));
$('scale').addEventListener('change', (e) => setSettings({ scale: Number(e.target.value) }));
