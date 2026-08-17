# -*- coding: utf-8 -*-
"""skin41 상세(detail.html)에 리훈 리뷰 위젯 <script> 1줄 삽입 → FTP 업로드 → 서버 재확인.
안전: 목업 블록 직후에만 삽입, 기존 태그 있으면 교체(중복 방지), 원본 백업 보관. skin41은 미공개 스킨(라이브 무영향).
"""
import sys, io, time
sys.path.insert(0, r'Z:\rihoon1\자동화\리훈메인디자인')
sys.stdout.reconfigure(encoding='utf-8')
from ftp_deploy import connect, BACKUP
import os, re

REMOTE = '/sde_design/skin41/product/detail.html'
BASE = 'https://rihoon.github.io/rihoon-reviews'
MARK = '<!-- ▲ 샘플 목업 끝 -->'
TAG_RE = re.compile(r'\s*<script[^>]*rihoon-reviews\.js[^>]*></script>')
TAG = f'\n            <script src="{BASE}/widget/rihoon-reviews.js?v={int(time.time())}" data-base="{BASE}/data" defer></script>'

ftp, _ = connect()
buf = io.BytesIO(); ftp.retrbinary('RETR ' + REMOTE, buf.write)
src = buf.getvalue().decode('utf-8')
os.makedirs(BACKUP, exist_ok=True)
bk = os.path.join(BACKUP, f'sde_design__skin41__product__detail.html.bak_reviewwidget_{time.strftime("%m%d%H%M")}')
open(bk, 'w', encoding='utf-8', newline='').write(src)
print('backup:', bk, len(src))

new = TAG_RE.sub('', src)
assert MARK in new, '삽입 마커 없음'
new = new.replace(MARK, MARK + TAG, 1)
# 크리마 위젯 자리 제거 (대표 요청 2026-08-18): 빈 "리뷰" 영역 + 주석
new = re.sub(r'\s*<!-- 크리마 리뷰 위젯[^\n]*-->\s*<div class="crema-product-reviews"></div>', '', new)
new = new.replace('<div class="crema-product-reviews"></div>', '')
print('crema container removed:', 'crema-product-reviews"></div>' not in new)

if '--dry' in sys.argv:
    print('DRY: would insert:', TAG.strip()); sys.exit()
ftp.storbinary('STOR ' + REMOTE, io.BytesIO(new.encode('utf-8')))
buf2 = io.BytesIO(); ftp.retrbinary('RETR ' + REMOTE, buf2.write)
chk = buf2.getvalue().decode('utf-8')
print('uploaded. server has tag:', 'rihoon-reviews.js' in chk, '| size', len(chk))
ftp.quit()
