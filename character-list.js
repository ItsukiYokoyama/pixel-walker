// character-list.html の処理。拡張機能のページとして開く(chrome-extension://<ID>/character-list.html)。
// 拡張機能のページではインラインのスクリプトが禁止されているので、別ファイルにしている。
// 各キャラクターの「待機」ポーズを、絵のままの大きさで描いて拡大表示する(popup.js と同じ描き方)
const SCALE = 3;
const list = document.getElementById('list');
(async () => {
  for (const [i, { id, label, genre }] of PW.list.entries()) {
    await PW.load(id);
    const sprite = PW.render(PW.grids(id, 1).idle.g, PW.palette(id), 1, false);
    const canvas = document.createElement('canvas');
    canvas.width = sprite.width;
    canvas.height = sprite.height;
    canvas.getContext('2d').drawImage(sprite, 0, 0);
    canvas.style.width = sprite.width * SCALE + 'px';
    canvas.style.height = sprite.height * SCALE + 'px';

    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = '<div class="no"></div><div class="stage"></div><div class="name"></div><div class="id"></div>';
    card.querySelector('.no').textContent = 'No.' + (i + 1) + ' ' + genre;
    card.querySelector('.stage').appendChild(canvas);
    card.querySelector('.name').textContent = label;
    card.querySelector('.id').textContent = id;
    list.appendChild(card);
  }
})();
document.getElementById('count').textContent = PW.list.length + ' 種類';
