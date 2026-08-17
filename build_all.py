# -*- coding: utf-8 -*-
"""mapping.json 기준 전 상품 JSON 빌드. 한 상품에 소스 여러 개 = 합치기(중복 리뷰 제거 안 함: 다른 상품 리뷰라 원문 다름).
mapping.json: {"1475": ["12629011395_2026 이야기다이어리", "4960363460_이야기 날짜형 하반기다이어리"], ...}
"""
import sys, json, html, shutil
from pathlib import Path
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).parent
VOC = Path(r'Z:\rihoon1\리훈\15. 고객의소리')
MAP = HERE / 'mapping.json'; FEAT = HERE / 'featured'; OUT = HERE / 'data'
PAGE = 20

import hashlib
def _pkey(u): return hashlib.md5(u.encode()).hexdigest()[:12]

def photo_map(pno):
    """photos/{pno}/index.json → {원URL: 로컬상대경로}. 우리 호스팅으로 치환(네이버 CDN 핫링크 회피)."""
    p = HERE / 'photos' / str(pno) / 'index.json'
    if not p.exists(): return {}
    idx = json.loads(p.read_text(encoding='utf-8'))
    return {u: f'photos/{pno}/{k}.jpg' for k, u in idx.items() if (HERE / 'photos' / str(pno) / f'{k}.jpg').exists()}

def load_reviews(folder, pmap=None):
    pmap = pmap or {}
    f = VOC / folder / '후기' / '후기.xlsx'
    if not f.exists(): return []
    df = pd.read_excel(f)
    if '상태' in df: df = df[df['상태'].astype(str).str.upper() == 'NORMAL']
    df = df.dropna(subset=['리뷰내용'])
    out = []
    for _, r in df.iterrows():
        t = html.unescape(str(r['리뷰내용'])).strip()
        if not t: continue
        rec = {'r': int(r['평점']) if pd.notna(r['평점']) else None, 'd': str(r['작성일'])[:10], 'a': str(r['작성자']),
               't': t, 'h': int(r['도움수']) if pd.notna(r.get('도움수')) else 0, 'b': bool(r['베스트']) if '베스트' in r else False,
               's': folder.split('_')[0]}  # 출처 스마트스토어 번호
        for col in ('이미지', '사진', 'images'):
            if col in df.columns and pd.notna(r.get(col)) and str(r[col]).strip():
                ph = [u.strip() for u in str(r[col]).split(',') if u.strip().startswith('http')]
                # 우리 호스팅에 있는 사진만 사용(없으면 원URL 유지). 위젯은 data-base의 상위(=사이트 루트) 기준으로 photos/ 를 찾음
                ph = [pmap.get(u, u) for u in ph]
                if ph: rec['p'] = ph
                break
        out.append(rec)
    return out

def build_one(pno, folders):
    reviews = []
    pmap = photo_map(pno)
    for f in folders: reviews += load_reviews(f, pmap)
    reviews.sort(key=lambda x: x['d'], reverse=True)
    rated = [x['r'] for x in reviews if x['r']]
    d = OUT / str(pno)
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)
    pages = [reviews[i:i+PAGE] for i in range(0, len(reviews), PAGE)] or [[]]
    for i, pg in enumerate(pages, 1):
        (d / f'p{i}.json').write_text(json.dumps(pg, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    fp = FEAT / f'{pno}.json'
    photo_reviews = [x for x in reviews if x.get('p')]
    # 갤러리 기본값: 사진 있는 최신 리뷰의 첫 사진 24장 (대표가 featured 고르면 그게 우선)
    auto_gallery = [x['p'][0] for x in photo_reviews[:24]]
    summary = {'product_no': int(pno), 'sources': [f.split('_')[0] for f in folders], 'count': len(reviews),
               'photo_count': len(photo_reviews), 'gallery': auto_gallery,
               'avg': round(sum(rated)/len(rated), 2) if rated else None,
               'dist': {str(k): rated.count(k) for k in range(5, 0, -1)},
               'pages': len(pages), 'page_size': PAGE, 'first': pages[0],
               'featured': json.loads(fp.read_text(encoding='utf-8')) if fp.exists() else []}
    (d / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return len(reviews), summary['avg']

if __name__ == '__main__':
    m = json.loads(MAP.read_text(encoding='utf-8')) if MAP.exists() else {}
    if not m: print('mapping.json 비어있음'); sys.exit()
    tot = 0
    for pno, folders in m.items():
        if not folders: continue
        n, avg = build_one(pno, folders); tot += n
        print(f'#{pno}: {n:,}건 avg {avg} ← {len(folders)}소스')
    print(f'완료: {len([v for v in m.values() if v])}상품 / {tot:,}건')
