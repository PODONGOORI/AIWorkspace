#!/usr/bin/env python3
"""{{COVER_ILL}} 자리에 표지 일러스트를 data URI로 넣는다.
사용: python3 inline_assets.py 입력.html [출력.html]   (출력 생략 시 덮어쓰기)
"""
import base64, os, sys

here = os.path.dirname(os.path.abspath(__file__))
png = os.path.join(here, '..', 'assets', 'cover-illustration.png')
src = sys.argv[1]
dst = sys.argv[2] if len(sys.argv) > 2 else src
html = open(src, encoding='utf-8').read()
uri = 'data:image/png;base64,' + base64.b64encode(open(png, 'rb').read()).decode()
n = html.count('{{COVER_ILL}}')
open(dst, 'w', encoding='utf-8').write(html.replace('{{COVER_ILL}}', uri))
print(f'{n} placeholder(s) replaced -> {dst}')
