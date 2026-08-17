# -*- coding: utf-8 -*-
"""고객의소리 후기.xlsx의 이미지 URL → 다운로드 → 썸네일(긴변 480px, JPEG q82) → photos/{cafe24번호}/{해시}.jpg
+ photos/{cafe24번호}/index.json (원URL→로컬파일 매핑). 재실행 시 이미 받은 건 건너뜀.
사용: python fetch_photos.py <cafe24번호> <고객의소리폴더명> [--limit N]
"""
import sys, json, hashlib, io, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd, requests
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')

VOC = Path(r'Z:\rihoon1\리훈\15. 고객의소리')
HERE = Path(__file__).parent
MAXSIDE, Q = 480, 82
H = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://smartstore.naver.com/'}

def key(u): return hashlib.md5(u.encode()).hexdigest()[:12]

def grab(u, dst):
    r = requests.get(u, headers=H, timeout=20); r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)); im = im.convert('RGB')
    im.thumbnail((MAXSIDE, MAXSIDE))
    im.save(dst, 'JPEG', quality=Q, optimize=True)
    return dst.stat().st_size

def main(pno, folder, limit=None):
    df = pd.read_excel(VOC / folder / '후기' / '후기.xlsx')
    if '이미지' not in df.columns: print('이미지 컬럼 없음 — 수집기 재실행 필요'); return
    urls = []
    for cell in df['이미지'].dropna().astype(str):
        urls += [u.strip() for u in cell.split(',') if u.strip().startswith('http')]
    urls = list(dict.fromkeys(urls))
    if limit: urls = urls[:limit]
    out = HERE / 'photos' / str(pno); out.mkdir(parents=True, exist_ok=True)
    idxp = out / 'index.json'
    idx = json.loads(idxp.read_text(encoding='utf-8')) if idxp.exists() else {}
    todo = [u for u in urls if key(u) not in idx or not (out / f'{key(u)}.jpg').exists()]
    print(f'{pno}: url {len(urls)} / 이미 {len(urls)-len(todo)} / 받을 것 {len(todo)}')
    ok = fail = 0; tot = 0
    with ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(grab, u, out / f'{key(u)}.jpg'): u for u in todo}
        for i, f in enumerate(as_completed(futs), 1):
            u = futs[f]
            try:
                tot += f.result(); idx[key(u)] = u; ok += 1
            except Exception as e:
                fail += 1
            if i % 200 == 0:
                print(f'  {i}/{len(todo)} ok {ok} fail {fail}', flush=True)
                idxp.write_text(json.dumps(idx, ensure_ascii=False), encoding='utf-8')
    idxp.write_text(json.dumps(idx, ensure_ascii=False), encoding='utf-8')
    print(f'완료: ok {ok} fail {fail} | 이번 용량 {tot/1024/1024:.1f}MB | 총 {len(idx)}장')

if __name__ == '__main__':
    lim = None
    if '--limit' in sys.argv: lim = int(sys.argv[sys.argv.index('--limit')+1])
    main(sys.argv[1], sys.argv[2], lim)
