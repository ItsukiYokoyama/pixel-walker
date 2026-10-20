"""キャラクターの絵データ(chars/<id>.json)・一覧(chars.js)・名前の翻訳(_locales)を、tools/ の元データからすべて作り直す。
ドット絵の元データ(tools/sprites/)から作るもの、骨組みや部品から描くもの、既存のキャラクターから派生させるものがある。

使い方: python3 tools/build.py   (Python 3 の標準ライブラリだけで動く)
"""
import json, re, sys
import os
from pwlib import CHARS, CHAR_DIR, ROOT, encode
import humanoid, vehicle, derive as dv
from roster_sprites import SPRITES
from roster_people import PEOPLE
from roster_vehicles import VEHICLES
from roster_creatures import CREATURES
from roster_derived import DERIVED

GENRES = ['people', 'animals', 'birds', 'sea', 'vehicles', 'fantasy']
SPRITE_DIR = os.path.join(ROOT, 'tools', 'sprites')
HEADER = ('// 自動生成(tools/build.py)。直接編集しないこと。\n'
          '// PW_INDEX: [id, 名前, ジャンル] の一覧。絵データは chars/<id>.json (使う 1 体だけ読み込む)。\n'
          '// 行は「文字+連続数」の連長圧縮。文字: k=輪郭 e=目 q=ハイライト その他=キャラごとのパレットの色\n')


def sprite(cid):
    """ドット絵の元データ(tools/sprites/<id>.json。行は圧縮しない)を、chars/<id>.json と同じ形にする"""
    src = json.load(open(os.path.join(SPRITE_DIR, cid + '.json'), encoding='utf-8'))
    frames = {}
    for name, f in src['frames'].items():
        d = {'rows': [encode(list(r)) for r in f['rows']], 'ax': f['ax']}
        if f.get('ledgeRow') is not None:
            d['ledgeRow'] = f['ledgeRow']
        frames[name] = d
    d = {'palette': src['palette'], 'unit': src['unit'], 'fine': src['fine'], 'frames': frames}
    if src.get('swim'):
        d['swim'] = src['swim']
    return d


def pack(frames, colors, extra=None):
    used = set()
    fr = {}
    for name, f in frames.items():
        rows = [encode(r) for r in f['g']]
        for r in f['g']:
            used.update(r)
        d = {'rows': rows, 'ax': f['ax']}
        if f.get('ledgeRow') is not None:
            d['ledgeRow'] = f['ledgeRow']
        fr[name] = d
    used.discard('.')
    missing = used - set(colors)
    assert not missing, missing
    pal = {k: colors[k] for k in sorted(used | {'k', 'e', 'q'}, key=lambda c: (c not in 'keq', c)) if k in colors}
    d = {'palette': pal, 'unit': 0.5, 'fine': True}
    if extra:
        d.update(extra)
    d['frames'] = fr
    return d


def tuples(fr):
    return {n: {'g': g, 'ax': ax, 'ledgeRow': L} for n, (g, ax, L) in fr.items()}


LOCALES = ['en', 'es_419', 'ko', 'pt_BR', 'zh_CN', 'zh_TW']


def write_locales(entries):
    """_locales/*/messages.json に、キャラクター名(char_<id>)とジャンル名(genre_<ジャンル>)を書く"""
    from i18n_names import NAMES, GENRES as GNAMES
    for loc in ['ja'] + LOCALES:
        path = os.path.join(ROOT, '_locales', loc, 'messages.json')
        old = json.load(open(path, encoding='utf-8'))
        out = {k: v for k, v in old.items() if not k.startswith(('char_', 'genre_'))}
        for cid, label, genre, _ in entries:
            msg = label if loc == 'ja' else NAMES[cid][LOCALES.index(loc)]
            out['char_' + cid] = {'message': msg}
        for g in GENRES:
            out['genre_' + g] = {'message': GNAMES[g][0 if loc == 'ja' else LOCALES.index(loc) + 1]}
        open(path, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=2) + '\n')


def check():
    """キャラクターを追加したときによくある間違いを、作り直す前に見つける"""
    from i18n_names import NAMES
    errors = []
    tables = [('roster_sprites.py', SPRITES), ('roster_people.py', PEOPLE), ('roster_vehicles.py', VEHICLES),
              ('roster_creatures.py', CREATURES), ('roster_derived.py', DERIVED)]
    seen = {}
    for fname, table in tables:
        for cid, val in table.items():
            if not re.fullmatch(r'[a-z0-9_]+', cid):
                errors.append(f'{fname}: id "{cid}" は英小文字・数字・_ だけにしてください')
            if cid in seen:
                errors.append(f'{fname}: id "{cid}" は {seen[cid]} と重複しています')
            seen[cid] = fname
            genre = 'vehicles' if table is VEHICLES else val[1]
            if genre not in GENRES:
                errors.append(f'{fname}: {cid} のジャンル "{genre}" は {", ".join(GENRES)} のどれかにしてください')
            if cid not in NAMES:
                errors.append(f'i18n_names.py: {cid} の名前の翻訳 (en, es_419, ko, pt_BR, zh_CN, zh_TW) がありません')
            elif len(NAMES[cid]) != len(LOCALES):
                errors.append(f'i18n_names.py: {cid} の翻訳は {len(LOCALES)} 個 (en, es_419, ko, pt_BR, zh_CN, zh_TW) 書いてください')
    for cid in SPRITES:
        if not os.path.exists(os.path.join(SPRITE_DIR, cid + '.json')):
            errors.append(f'roster_sprites.py: {cid} の元データ tools/sprites/{cid}.json がありません')
    for cid, (_, _, base, _) in DERIVED.items():
        if base not in SPRITES:
            errors.append(f'roster_derived.py: {cid} の元のキャラクター "{base}" は roster_sprites.py にありません')
    if errors:
        sys.exit('キャラクターの定義に問題があります:\n  ' + '\n  '.join(errors))


def main():
    check()
    D = {cid: sprite(cid) for cid in SPRITES}  # 派生キャラクターの元にもなる
    entries = []  # (id, 名前, ジャンル, JSON 文字列)
    new = [(cid, label, genre, D[cid]) for cid, (label, genre) in SPRITES.items()]
    for cid, (label, genre, look) in PEOPLE.items():
        fr, colors = humanoid.frames(look)
        new.append((cid, label, genre, pack(tuples(fr), colors)))
    for cid, (label, genre, base, spec) in DERIVED.items():
        fr, colors = dv.derive(D[base], spec)
        extra = {'swim': D[base]['swim']} if D[base].get('swim') else None
        new.append((cid, label, genre, pack(fr, colors, extra)))
    for table, genre0 in ((VEHICLES, 'vehicles'), (CREATURES, None)):
        for cid, val in table.items():
            if genre0:
                label, spec = val
                genre = genre0
            else:
                label, genre, spec = val
            fr, colors = vehicle.frames(spec)
            extra = {'swim': {'frames': ['walk1', 'walk2'], 'speed': spec.get('speed', 1)}} if spec.get('fly') else None
            new.append((cid, label, genre, pack(tuples(fr), colors, extra)))
    for cid, label, genre, d in new:
        entries.append((cid, label, genre, json.dumps(d, ensure_ascii=False, separators=(',', ':'))))
    # ジャンル順に並べる(同じジャンルの中は元の順)
    order = {g: i for i, g in enumerate(GENRES)}
    entries.sort(key=lambda e: order[e[2]])
    # 絵データ: chars/<id>.json(使う 1 体だけを読み込む)
    os.makedirs(CHAR_DIR, exist_ok=True)
    keep = set()
    total = 0
    for cid, label, genre, s in entries:
        p = os.path.join(CHAR_DIR, cid + '.json')
        open(p, 'w', encoding='utf-8').write(s)
        keep.add(cid + '.json')
        total += len(s.encode())
    for f in os.listdir(CHAR_DIR):
        if f.endswith('.json') and f not in keep:
            os.remove(os.path.join(CHAR_DIR, f))
    # 一覧: chars.js
    lines = [HEADER + 'window.PW_INDEX = ' + json.dumps([[e[0], e[1], e[2]] for e in entries], ensure_ascii=False,
                                                       separators=(',', ':')) + ';',
             'window.PW_GENRES = ' + json.dumps(GENRES) + ';']
    open(CHARS, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    write_locales(entries)
    from collections import Counter
    print(len(entries), 'characters', dict(Counter(e[2] for e in entries)))
    print('chars/*.json', round(total / 1024), 'KB in total')


if __name__ == '__main__':
    main()
