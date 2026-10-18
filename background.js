// service worker。Webページで動く content.js から頼まれて、キャラクターの絵データ(chars/<id>.json)を読んで返すだけ。
// 読むのは拡張機能の中のファイルで、外部とは一切通信しない。
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || msg.type !== 'pw-char' || !/^\w+$/.test(msg.id || '')) return;
  fetch(chrome.runtime.getURL(`chars/${msg.id}.json`))
    .then((r) => (r.ok ? r.text() : Promise.reject(new Error(r.status))))
    .then((text) => sendResponse({ text }))
    .catch(() => sendResponse({}));
  return true; // 非同期で返す
});
