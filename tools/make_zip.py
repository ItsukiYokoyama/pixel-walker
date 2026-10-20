"""配布用の zip を作る。コミットされているファイルから、拡張機能の動作に必要なものだけを入れる。

使い方: python3 tools/make_zip.py   → dist/pixel-walker-<manifest.json の version>.zip
        (ファイルは zip のいちばん上に直接入れる。Windows・Mac で展開するとできるフォルダに manifest.json が入り、
         そのまま「パッケージ化されていない拡張機能を読み込む」で選べる)
"""
import json, os, subprocess, sys, zipfile
from pwlib import ROOT

# 拡張機能の動作には不要な、開発用のファイル
SKIP = ('tools/', 'docs/', '.github/', '.gitignore', 'README.md', 'CONTRIBUTING.md')


def main():
    if subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        sys.exit('コミットしていない変更があります。コミットしてから作ってください')
    version = json.load(open(os.path.join(ROOT, 'manifest.json'), encoding='utf-8'))['version']
    files = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, text=True).stdout.split('\0')
    files = sorted(f for f in files if f and not f.startswith(SKIP))
    os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
    out = os.path.join(ROOT, 'dist', f'pixel-walker-{version}.zip')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(ROOT, f), f)
    print(out, f'({len(files)} files)')


if __name__ == '__main__':
    main()
