# -*- coding: utf-8 -*-
"""리훈 리뷰 매핑 웹앱 (크리마식) — 스마트스토어 리뷰 소스 ↔ 자사몰(cafe24) 상품 매핑, 합치기/중복 붙이기, 빌드·배포.
실행: cd Z:\rihoon1\자동화\리뷰위젯 && streamlit run app.py --server.port 5614
"""
import sys, json, subprocess, re
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.insert(0, r'C:\Users\rihoo\projects\rihoon-keywords')
HERE = Path(__file__).parent
VOC = Path(r'Z:\rihoon1\리훈\15. 고객의소리')
MAP = HERE / 'mapping.json'          # {cafe24_no: [source_folder, ...]}
FEAT = HERE / 'featured'
DATA = HERE / 'data'

st.set_page_config(page_title='리훈 리뷰 매핑', layout='wide')
st.markdown("""<style>
@import url('https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2/fonts/variable/woff2/SUIT-Variable.css');
html,body,[class*="css"]{font-family:"SUIT Variable",sans-serif!important}
.stApp{background:#fff}
h1,h2,h3{letter-spacing:-.02em;color:#1a1a1a}
.src{padding:8px 10px;border:1px solid #e7e5e1;margin-bottom:6px;font-size:13px}
.muted{color:#8a8783;font-size:12px}
div[data-testid="stMetricValue"]{font-size:22px}
</style>""", unsafe_allow_html=True)

# ── 로더 ──
@st.cache_data(ttl=300)
def load_sources():
    rows = []
    for d in sorted(VOC.iterdir()):
        if not d.is_dir() or '_' not in d.name: continue
        f = d / '후기' / '후기.xlsx'
        n = 0; last = ''
        if f.exists():
            try:
                df = pd.read_excel(f, usecols=['작성일'])
                n = len(df); last = str(df['작성일'].max())[:10]
            except Exception: pass
        ss, name = d.name.split('_', 1)
        rows.append({'folder': d.name, 'ss_no': ss, 'name': name, 'count': n, 'last': last})
    return pd.DataFrame(rows)

@st.cache_data(ttl=600)
def load_products():
    import cafe24
    out, off = [], 0
    while True:
        r = cafe24.api('GET', f'/admin/products?limit=100&offset={off}&display=T')
        ps = r.get('products', [])
        for p in ps:
            out.append({'no': int(p['product_no']), 'name': p['product_name'], 'selling': p.get('selling') == 'T'})
        if len(ps) < 100: break
        off += 100
    return pd.DataFrame(out).sort_values('no', ascending=False)

def load_map():
    return json.loads(MAP.read_text(encoding='utf-8')) if MAP.exists() else {}
def save_map(m):
    MAP.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')

# ── 상단 ──
st.title('리훈 리뷰 매핑')
st.caption('스마트스토어 리뷰(고객의소리)를 자사몰 상품에 붙입니다. 여러 소스를 한 상품에 = 합치기 · 한 소스를 여러 상품에 = 중복. 네이버쇼핑 카운트엔 영향 없음(격리 저장).')

src = load_sources()
try:
    prods = load_products()
except Exception as e:
    st.error(f'cafe24 상품 로드 실패: {e}'); st.stop()
mapping = load_map()

c1, c2, c3, c4 = st.columns(4)
c1.metric('리뷰 소스(폴더)', len(src)); c2.metric('소스 리뷰 합계', f"{int(src['count'].sum()):,}")
c3.metric('자사몰 진열상품', len(prods)); c4.metric('매핑된 상품', len([k for k, v in mapping.items() if v]))

# ── 크리마 CSV import ──
with st.expander('크리마 CSV로 초기 매핑 가져오기 (쇼핑몰 상품번호 ↔ 스마트스토어 상품번호)'):
    up = st.file_uploader('크리마 > 외부리뷰연동 > CSV 다운로드 파일', type=['csv'])
    if up is not None:
        try:
            df = pd.read_csv(up, dtype=str)
        except Exception:
            up.seek(0); df = pd.read_csv(up, dtype=str, encoding='cp949')
        st.dataframe(df.head(), use_container_width=True)
        cols = list(df.columns)
        cc = st.selectbox('쇼핑몰(cafe24) 상품번호 컬럼', cols, index=0)
        sc = st.selectbox('스마트스토어 상품번호 컬럼', cols, index=min(2, len(cols)-1))
        if st.button('가져와서 매핑에 병합'):
            ss2folder = dict(zip(src['ss_no'], src['folder']))
            added = 0
            for _, r in df.iterrows():
                cno = str(r[cc]).strip(); ssn = str(r[sc]).strip()
                for one in re.split(r'[,\s]+', ssn):
                    if one in ss2folder:
                        mapping.setdefault(cno, [])
                        if ss2folder[one] not in mapping[cno]:
                            mapping[cno].append(ss2folder[one]); added += 1
            save_map(mapping); st.success(f'{added}개 연결 추가'); st.rerun()

st.divider()
L, R = st.columns([1, 1.2])

# ── 좌: 소스 목록 ──
with L:
    st.subheader('리뷰 소스 (스마트스토어)')
    q = st.text_input('소스 검색', placeholder='이야기, 오늘기억…', key='qs')
    view = src if not q else src[src['name'].str.contains(q, case=False, na=False)]
    used = {f for v in mapping.values() for f in v}
    for _, r in view.sort_values('count', ascending=False).iterrows():
        tag = '🔗' if r['folder'] in used else '·'
        st.markdown(f"<div class='src'>{tag} <b>{r['name']}</b> <span class='muted'>#{r['ss_no']} · {r['count']:,}건 · 최근 {r['last']}</span></div>", unsafe_allow_html=True)

# ── 우: 상품 선택 → 매핑 편집 ──
with R:
    st.subheader('자사몰 상품 → 붙일 소스')
    qp = st.text_input('상품 검색', placeholder='상품명 또는 번호', key='qp')
    pv = prods if not qp else prods[prods['name'].str.contains(qp, case=False, na=False) | prods['no'].astype(str).str.contains(qp)]
    labels = [f"#{r['no']}  {r['name'][:48]}  " + ('' if str(r['no']) not in mapping or not mapping[str(r['no'])] else f"[{sum(int(src[src['folder']==f]['count'].iloc[0]) for f in mapping[str(r['no'])] if (src['folder']==f).any()):,}]") for _, r in pv.iterrows()]
    if not labels:
        st.info('검색 결과 없음')
    else:
        pick = st.selectbox('상품 선택', labels, key='pick')
        pno = str(int(re.match(r'#(\d+)', pick).group(1)))
        cur = mapping.get(pno, [])
        st.markdown(f"**선택: #{pno}** · 현재 {len(cur)}개 소스 연결")
        opts = list(src.sort_values('count', ascending=False)['folder'])
        fmt = lambda f: f"{src[src['folder']==f]['name'].iloc[0]}  ({int(src[src['folder']==f]['count'].iloc[0]):,}건)"
        sel = st.multiselect('붙일 소스 (여러 개 선택 = 합치기)', opts, default=[c for c in cur if c in opts], format_func=fmt, key=f'ms_{pno}')
        tot = sum(int(src[src['folder']==f]['count'].iloc[0]) for f in sel)
        st.caption(f'합계 {tot:,}건이 #{pno}에 표시됩니다.')
        b1, b2 = st.columns(2)
        if b1.button('이 상품 매핑 저장', type='primary'):
            mapping[pno] = sel; save_map(mapping); st.success('저장됨'); st.rerun()
        if b2.button('이 상품 매핑 비우기'):
            mapping.pop(pno, None); save_map(mapping); st.rerun()

        # 상단 포토리뷰 선택 — 우리 호스팅에 받아둔 리뷰 사진을 썸네일로 보고 체크
        with st.expander('상단 포토리뷰 선택 (사진 잘 나온 것 고르기)', expanded=False):
            pdir = HERE / 'photos' / pno; idxp = pdir / 'index.json'
            fp = FEAT / f'{pno}.json'
            cur_f = json.loads(fp.read_text(encoding='utf-8')) if fp.exists() else []
            if not idxp.exists():
                st.info(f'받아둔 사진 없음. 먼저: python fetch_photos.py {pno} <고객의소리폴더명>')
            else:
                idx = json.loads(idxp.read_text(encoding='utf-8'))
                files = [f'photos/{pno}/{k}.jpg' for k in idx if (pdir / f'{k}.jpg').exists()]
                st.caption(f'받아둔 사진 {len(files):,}장 · 현재 선택 {len(cur_f)}장. 체크한 순서대로 상단 갤러리에 노출.')
                per = 48
                pg = st.number_input('페이지', 1, max(1, (len(files)+per-1)//per), 1, key=f'pg_{pno}')
                chunk = files[(pg-1)*per: pg*per]
                sel = set(cur_f)
                cols = st.columns(8)
                for i, rel in enumerate(chunk):
                    with cols[i % 8]:
                        st.image(str(HERE / rel), use_container_width=True)
                        if st.checkbox('선택', value=rel in sel, key=f'ck_{pno}_{rel}'):
                            sel.add(rel)
                        else:
                            sel.discard(rel)
                # 순서: 기존 순서 유지 + 새로 체크한 것 뒤에
                new_f = [u for u in cur_f if u in sel] + [u for u in chunk if u in sel and u not in cur_f]
                c_a, c_b = st.columns(2)
                if c_a.button('선택 저장 (featured)', key=f'sv_{pno}'):
                    FEAT.mkdir(exist_ok=True); fp.write_text(json.dumps(new_f, ensure_ascii=False), encoding='utf-8'); st.success(f'{len(new_f)}장 저장'); st.rerun()
                if c_b.button('선택 전부 해제', key=f'cl_{pno}'):
                    if fp.exists(): fp.unlink()
                    st.rerun()

st.divider()
# ── 빌드·배포 ──
st.subheader('빌드 · 배포')
st.caption('mapping.json 기준으로 상품별 JSON을 생성하고 GitHub Pages로 푸시합니다. (자사몰 위젯이 즉시 새 데이터를 읽음)')
cb1, cb2 = st.columns(2)
if cb1.button('① 전 상품 JSON 빌드'):
    log = subprocess.run([sys.executable, str(HERE / 'build_all.py')], capture_output=True, text=True, encoding='utf-8', cwd=str(HERE))
    st.code((log.stdout or '') + (log.stderr or ''))
if cb2.button('② GitHub 푸시(배포)'):
    cmds = [['git', 'add', '-A'], ['git', '-c', 'user.name=rihoon', '-c', 'user.email=rihoon79@gmail.com', 'commit', '-qm', 'data: rebuild from mapping app'], ['git', 'push', '-q', 'origin', 'master']]
    out = ''
    for c in cmds:
        r = subprocess.run(c, capture_output=True, text=True, encoding='utf-8', cwd=str(HERE)); out += ' '.join(c) + '\n' + (r.stdout or '') + (r.stderr or '')
    st.code(out or '완료')
