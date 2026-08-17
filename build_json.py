# -*- coding: utf-8 -*-
"""고객의소리 후기.xlsx → 위젯용 JSON. 격리 저장(cafe24 리뷰시스템 무접촉).
사용: python build_json.py <cafe24상품번호> <고객의소리폴더명>
"""
import sys, json, re, html
from pathlib import Path
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r'Z:\rihoon1\리훈\15. 고객의소리')
OUT = Path(__file__).parent / 'data'
OUT.mkdir(exist_ok=True)

def build(cafe24_no, folder):
    f = ROOT / folder / '후기' / '후기.xlsx'
    df = pd.read_excel(f)
    df = df[df['상태'].astype(str).str.upper() == 'NORMAL'] if '상태' in df else df
    df = df.dropna(subset=['리뷰내용'])
    reviews = []
    for _, r in df.iterrows():
        txt = html.unescape(str(r['리뷰내용'])).strip()
        if not txt: continue
        reviews.append({
            'r': int(r['평점']) if pd.notna(r['평점']) else None,
            'd': str(r['작성일'])[:10],
            'a': str(r['작성자']),
            't': txt,
            'h': int(r['도움수']) if pd.notna(r.get('도움수')) else 0,
            'b': bool(r['베스트']) if '베스트' in r else False,
        })
    reviews.sort(key=lambda x: x['d'], reverse=True)
    rated = [x['r'] for x in reviews if x['r']]
    dist = {str(k): rated.count(k) for k in range(5, 0, -1)}
    out = {
        'product_no': int(cafe24_no),
        'ss_product_no': folder.split('_')[0],
        'count': len(reviews),
        'avg': round(sum(rated)/len(rated), 2) if rated else None,
        'dist': dist,
        'reviews': reviews,
    }
    # 요약(첫 로드) + 페이지 파일(20개씩) — 위젯이 가볍게 시작하고 '더보기'로 이어받음
    PAGE = 20
    d = OUT / str(cafe24_no); d.mkdir(exist_ok=True)
    pages = [reviews[i:i+PAGE] for i in range(0, len(reviews), PAGE)] or [[]]
    for i, pg in enumerate(pages, 1):
        (d / f'p{i}.json').write_text(json.dumps(pg, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    summary = {k: v for k, v in out.items() if k != 'reviews'}
    summary['pages'] = len(pages); summary['page_size'] = PAGE
    summary['first'] = pages[0]
    (d / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'{cafe24_no} ← {folder}: {len(reviews)}건 avg {out["avg"]} dist {dist} → data/{cafe24_no}/summary.json + {len(pages)} pages')

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
