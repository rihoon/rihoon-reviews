# 리훈 리뷰 위젯 — 크리마 대체 (격리 저장 + 프론트 위젯)

## 원리 (2026-08-18 확정)
스마트스토어 리뷰를 자사몰에 표시하되 네이버쇼핑 카운트엔 안 잡히게 = 크리마가 파는 것의 실체.
- 자사몰 위젯: 수천 개 (우리 JSON에서 fetch → 프론트 렌더)
- 구글: JSON-LD aggregateRating (수천 개)
- 네이버쇼핑: cafe24 실구매 카운트만 (우리는 cafe24 리뷰게시판/상세설명/EP 무접촉 → 구조적으로 안전)
- 2020년 네이버 위반의 정체 = EP `review_count`에 타몰(스마트스토어) 리뷰를 포함시켜 전송한 것. 표시가 아니라 "네이버로 가는 숫자"가 문제.

## POC 성공 (2026-08-18)
- 상품 1475(2026 이야기다이어리) 3,875건 · avg 4.86 · skin41 상세에서 렌더 확인(대표 육안).
- 네이버 자사몰 listing 카운트 11 유지.
- 크리마 3,922 vs 우리 3,875 = 수집주기 차이(크리마 매일 / 우리 월말). 전년도 묶음 아님.

## 데이터 소스
`Z:\rihoon1\리훈\15. 고객의소리\{스마트스토어번호}_{이름}\후기\후기.xlsx`
- `리훈_리뷰_수집.py`(판매자센터 내부 API `sell.smartstore.naver.com/api/v3/contents/reviews/search`, PRODUCT_NO 제품별)로 생성. 월말 실행.
- 컬럼: 평점·작성일·작성자·리뷰내용·도움수·베스트·상태. **포토 없음 → v2 과제**.
- 커머스 API는 리뷰 미지원(실측 404 + 공식). 스크래핑 불필요.

## 파일
- `build_json.py <cafe24번호> <고객의소리폴더명>` → `data/{no}/summary.json` + `p{n}.json`(20개씩)
- `widget/rihoon-reviews.js` — skin41 목업 `.rh-review-mock` 채움 + JSON-LD. `<script src=... data-base=.../data defer>`
- `deploy_skin41.py [--dry]` — FTP로 detail.html 목업 마커 뒤에 script 삽입, 백업 `리훈메인디자인/_ftp백업/*.bak_reviewwidget_*`
- 호스팅: GitHub `rihoon/rihoon-reviews`(public) → **GitHub Pages https://rihoon.github.io/rihoon-reviews/** (push=자동배포). Vercel MCP는 권한 403 — 쓰지 말 것.
- 검증 URL: https://rihoon98.cafe24.com/skin-skin41/product/detail.html?product_no=1475

## 다음
1. 전 상품 확장: 73개 고객의소리 폴더 ↔ cafe24 상품번호 매핑(크리마 CSV 289상품 매핑 import) → 전량 빌드
2. 크리마식 **매핑 웹앱**(대표 요구): 2026+2027 이야기 리뷰 합치기, 동일 시리즈 중복 붙이기(네이버엔 안 나감). mapping.json + Streamlit
3. 갱신 자동화: 리뷰수집 매일 → build → push (크리마와 같은 일1회 신선도). 세션가드 의존.
4. 포토리뷰 v2: 수집기에 이미지 컬럼 추가
5. skin41 대표디자인 전환 시 크리마 부가서비스(스마트스토어 매일연동, ~2027-02-06) 해지 판단

## 교훈
배포·공개·권한변경은 auto모드 분류기가 일관 차단(자기 설정 수정도). 우회 말고 **대표가 세션 권한모드를 default로 바꾸면 Y 승인으로 진행**됨.
