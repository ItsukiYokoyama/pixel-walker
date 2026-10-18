// 新しいバージョンの確認(設定画面 = ポップアップでだけ使う)。
// ポップアップを開いたときに、1 日 1 回まで ditsuki.com の公開ファイル(最新のバージョン番号)を読む。
// 送るのは通常の Web ページの読み込みと同じ情報だけで、ページの内容や設定は送らない。設定でオフにできる。
// サイト側は GitHub の Releases をもとに latest.json を返す(googleExWebSite の ReleaseController)。
(() => {
  const LATEST_URL = 'https://ditsuki.com/pixel-walker/latest.json';
  const KEY = 'pw-update'; // chrome.storage.local: { checkedAt, version }
  const INTERVAL = 24 * 60 * 60 * 1000; // 確認の間隔
  const RETRY = 60 * 60 * 1000; // 失敗したときは 1 時間あけてから試す

  // a が b より新しいバージョンか(1.2.10 > 1.2.9 のように数字で比べる)
  function isNewer(a, b) {
    const pa = String(a).split('.').map((n) => parseInt(n, 10) || 0);
    const pb = String(b).split('.').map((n) => parseInt(n, 10) || 0);
    for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
      if ((pa[i] || 0) !== (pb[i] || 0)) return (pa[i] || 0) > (pb[i] || 0);
    }
    return false;
  }

  // 最新のバージョン番号。前回の確認から INTERVAL 経っていなければ、保存した値を使う。分からなければ null
  async function latestVersion() {
    const { [KEY]: saved } = await chrome.storage.local.get(KEY);
    if (saved && Date.now() - saved.checkedAt < INTERVAL) return saved.version || null;
    try {
      const res = await fetch(LATEST_URL, { cache: 'no-store', credentials: 'omit', signal: AbortSignal.timeout(5000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const { version } = await res.json();
      if (!/^\d+(\.\d+)*$/.test(String(version))) throw new Error('bad version');
      await chrome.storage.local.set({ [KEY]: { checkedAt: Date.now(), version: String(version) } });
      return String(version);
    } catch {
      await chrome.storage.local.set({ [KEY]: { checkedAt: Date.now() - INTERVAL + RETRY, version: saved?.version } });
      return saved?.version || null;
    }
  }

  // 今のバージョンより新しいものがあれば、そのバージョン番号。無ければ null
  async function check() {
    const latest = await latestVersion();
    const current = chrome.runtime.getManifest().version;
    return latest && isNewer(latest, current) ? latest : null;
  }

  window.PWUpdate = { check, isNewer };
})();
