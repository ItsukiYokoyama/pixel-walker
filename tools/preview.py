"""キャラクターの全ポーズを並べた確認用の画像を作る(PR に貼る用)。

使い方: python3 tools/preview.py <id> [<id> ...]   (先に tools/build.py で絵データを作っておく)
        → preview/<id>.png に、待機・歩き・ジャンプ・落下・座る・寝る・ぶら下がり・よじ登りを 1 枚に並べる
"""
import json, os, sys
from pwlib import CHAR_DIR, ROOT, decode, palette, sheet

ORDER = ['idle', 'walk1', 'walk3', 'walk2', 'walk4', 'jump', 'fall', 'sit', 'sleep',
         'hang1', 'hang2', 'pull1', 'pull2', 'pull3']


def main(ids):
    if not ids:
        sys.exit(__doc__)
    out_dir = os.path.join(ROOT, 'preview')
    os.makedirs(out_dir, exist_ok=True)
    for cid in ids:
        path = os.path.join(CHAR_DIR, cid + '.json')
        if not os.path.exists(path):
            sys.exit(f'{cid}: chars/{cid}.json がありません。先に python3 tools/build.py を実行してください')
        d = json.load(open(path, encoding='utf-8'))
        pal = palette(d)
        names = [n for n in ORDER if n in d['frames']]
        items = [([decode(r) for r in d['frames'][n]['rows']], pal) for n in names]
        out = os.path.join(out_dir, cid + '.png')
        sheet(out, items, scale=4, cols=7, cell=(44, 48))
        print(out, '(' + ' / '.join(names) + ')')


if __name__ == '__main__':
    main(sys.argv[1:])
