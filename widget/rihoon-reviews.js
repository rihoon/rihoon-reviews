/* 리훈 리뷰 위젯 v1.4 — 격리 저장소(JSON) → skin41 .rh-review-mock 채우기 + JSON-LD.
 * 안전원칙: cafe24 상품후기 게시판/상세설명/EP 무접촉. 오직 별도 fetch → 프론트 렌더.
 * v1.1: 긴 리뷰 4줄 접기(더보기), 상단 포토갤러리=대표가 고른 featured만 노출.
 * 사용: <script src=".../rihoon-reviews.js" data-base="https://<host>/data" defer></script>
 */
(function () {
  var s = document.currentScript;
  var BASE = (s && s.getAttribute('data-base')) || '';
  var m = location.search.match(/product_no=(\d+)/);
  var PNO = (s && s.getAttribute('data-product')) || (m && m[1]);
  if (!PNO || !BASE) return;

  var root = document.querySelector('.rh-review-mock');
  if (!root) return;

  // ── 스타일(위젯 전용, 목업 CSS 위에 얹음) ──
  var css = document.createElement('style');
  css.textContent =
    '.rh-review-mock .rhrv-text{display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;white-space:pre-line}' +
    '.rh-review-mock .rhrv-item.is-open .rhrv-text{display:block;-webkit-line-clamp:unset;overflow:visible}' +
    '.rh-review-mock .rhrv-toggle{display:none;margin-top:6px;font-size:12px;color:#8a8783;cursor:pointer;background:none;border:0;padding:0;font-family:inherit}' +
    '.rh-review-mock .rhrv-item.is-long .rhrv-toggle{display:inline-block}' +
    '.rh-review-mock .rhrv-toggle:hover{color:#1a1a1a;text-decoration:underline}' +
    '.rh-review-mock .rhrv-gallery .rhrv-ph{flex:0 0 auto;width:92px;height:92px;border-radius:0;overflow:hidden;background:#f2f0ec;cursor:pointer}' +
    '.rh-review-mock .rhrv-gallery .rhrv-ph img{width:100%;height:100%;object-fit:cover;display:block}' +
    /* 카드 = 좌 글 / 우 사진 2단 (사진 없으면 글 전폭). 세로 길이 절감 */
    '.rh-review-mock .rhrv-item{display:flex;gap:20px;align-items:flex-start}' +
    '.rh-review-mock .rhrv-body{flex:1 1 auto;min-width:0}' +
    '.rh-review-mock .rhrv-photos{flex:0 0 auto;display:grid;grid-template-columns:repeat(2,96px);gap:6px;margin:0}' +
    '.rh-review-mock .rhrv-photos img{width:96px;height:96px;object-fit:cover;display:block;cursor:pointer;background:#f2f0ec}' +
    '.rh-review-mock .rhrv-photos.n1{grid-template-columns:96px}' +
    '.rh-review-mock .rhrv-photos .rhrv-morecnt{width:96px;height:96px;display:flex;align-items:center;justify-content:center;background:#f2f0ec;font-size:13px;color:#4a4a4a;cursor:pointer}' +
    /* 좁은 컨테이너(≤520px)에서만 세로 전환 — 뷰포트가 아니라 리뷰 영역 폭 기준(container query) */
    '.rh-review-mock{container-type:inline-size}' +
    '@container (max-width:520px){.rh-review-mock .rhrv-item{flex-direction:column;gap:10px}.rh-review-mock .rhrv-photos{display:flex;flex-wrap:wrap}}' +
    '.rh-review-mock .rhrv-more{text-align:center;padding:14px;border:1px solid #e7e5e1;margin-top:16px;cursor:pointer;font-weight:700;font-size:14px}' +
    '.rh-review-mock .rhrv-more:hover{background:#faf9f7}' +
    '.rh-review-mock .rhrv-pager{display:flex;justify-content:center;align-items:center;gap:4px;padding:26px 0 8px;flex-wrap:wrap}' +
    '.rh-review-mock .rhrv-pg-btn{min-width:34px;height:34px;padding:0 8px;border:1px solid #e7e5e1;background:#fff;color:#4a4a4a;font-size:13px;font-family:inherit;cursor:pointer;border-radius:0}' +
    '.rh-review-mock .rhrv-pg-btn:hover:not(:disabled){border-color:#1a1a1a;color:#1a1a1a}' +
    '.rh-review-mock .rhrv-pg-btn.on{background:#1a1a1a;color:#fff;border-color:#1a1a1a;font-weight:700}' +
    '.rh-review-mock .rhrv-pg-btn:disabled{opacity:.35;cursor:default}' +
    '.rh-review-mock .rhrv-pg-dots{color:#8a8783;padding:0 4px;font-size:13px}' +
    '.rh-review-mock .rhrv-best-label{font-size:14px;font-weight:800;color:#1a1a1a;padding:22px 0 8px;border-bottom:2px solid #1a1a1a;margin-bottom:4px;letter-spacing:-.01em}' +
    '.rh-review-mock .rhrv-best .rhrv-item{background:#faf9f7;padding:18px 16px;margin-bottom:8px;border-bottom:0}' +
    '.rhrv-lb{display:none;position:fixed;inset:0;background:rgba(0,0,0,.82);z-index:99999;align-items:center;justify-content:center;cursor:zoom-out}' +
    '.rhrv-lb img{max-width:92vw;max-height:92vh;object-fit:contain;box-shadow:0 10px 40px rgba(0,0,0,.5)}';
  document.head.appendChild(css);

  // 사진은 사이트 루트(=data 상위)의 photos/ 아래. BASE가 상대경로여도 절대 URL로 정규화.
  var SITE = new URL(BASE.replace(/(^|\/)data\/?$/, '') || '.', location.href).href.replace(/\/$/, '');
  function url(u) { return /^https?:/.test(u) ? u : SITE + '/' + u.replace(/^\/+/, ''); }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  // 라이트박스(크게 보기)
  var lb = document.createElement('div'); lb.className = 'rhrv-lb'; lb.innerHTML = '<img alt="">';
  lb.addEventListener('click', function () { lb.style.display = 'none'; });
  document.body.appendChild(lb);
  root.addEventListener('click', function (e) {
    var im = e.target.closest('.rhrv-ph img, .rhrv-photos img, .rhrv-morecnt'); if (!im) return;
    lb.querySelector('img').src = im.getAttribute('data-full') || im.src; lb.style.display = 'flex';
  });
  function stars(n) { n = Math.round(n || 0); return '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n); }
  function fdate(d) { return (d || '').replace(/-/g, '.'); }
  function item(r) {
    var ps = r.p || [], MAX = 4;
    var shown = ps.slice(0, MAX).map(function (u, i) {
      // 마지막 칸에 남은 장수 표시(+N), 클릭 시 라이트박스로 순서대로
      if (i === MAX - 1 && ps.length > MAX) return '<div class="rhrv-morecnt" data-full="' + esc(url(u)) + '">+' + (ps.length - MAX + 1) + '</div>';
      return '<img src="' + esc(url(u)) + '" alt="리뷰 사진" loading="lazy">';
    }).join('');
    var pcls = ps.length === 1 ? ' n1' : '';
    return '<li class="rhrv-item"><div class="rhrv-body"><div class="rhrv-meta"><span class="rhrv-st">' + stars(r.r) +
      '</span><span class="rhrv-name">' + esc(r.a) + '</span><span class="rhrv-date">' + fdate(r.d) +
      '</span></div><p class="rhrv-text">' + esc(r.t) + '</p>' +
      '<button type="button" class="rhrv-toggle">더보기</button></div>' +
      (shown ? '<div class="rhrv-photos' + pcls + '">' + shown + '</div>' : '') + '</li>';
  }
  // 렌더 후: 4줄 넘는 리뷰만 '더보기' 표시
  function markLong(scope) {
    Array.prototype.forEach.call(scope.querySelectorAll('.rhrv-item:not([data-chk])'), function (li) {
      li.setAttribute('data-chk', '1');
      var p = li.querySelector('.rhrv-text');
      if (p && p.scrollHeight > p.clientHeight + 2) li.classList.add('is-long');
    });
  }
  root.addEventListener('click', function (e) {
    var b = e.target.closest('.rhrv-toggle'); if (!b) return;
    var li = b.closest('.rhrv-item'); li.classList.toggle('is-open');
    b.textContent = li.classList.contains('is-open') ? '접기' : '더보기';
  });

  var list = root.querySelector('.rhrv-list');
  var more = root.querySelector('.rhrv-more');
  var page = 1, pages = 1;
  function loadPage(n) { return fetch(BASE + '/' + PNO + '/p' + n + '.json').then(function (r) { return r.json(); }); }

  fetch(BASE + '/' + PNO + '/summary.json').then(function (r) { return r.json(); }).then(function (S) {
    var sc = root.querySelector('.rhrv-score'); if (sc) sc.textContent = (S.avg || 0).toFixed(1);
    var st = root.querySelector('.rhrv-stars'); if (st) st.textContent = stars(S.avg);
    var tot = root.querySelector('.rhrv-total b'); if (tot) tot.textContent = S.count.toLocaleString();

    // 상단 포토갤러리: 대표가 고른 featured(사진 URL 목록)만. 없으면 숨김.
    var gw = root.querySelector('.rhrv-gallery-wrap'), g = root.querySelector('.rhrv-gallery');
    // 대표가 고른 featured 우선, 없으면 자동 갤러리(사진 있는 최신 리뷰)
    var feat = (S.featured && S.featured.length) ? S.featured : (S.gallery || []);
    if (gw) gw.style.display = feat.length ? '' : 'none';
    var gl = root.querySelector('.rhrv-gallery-label');
    if (gl && S.photo_count) gl.textContent = '고객 포토리뷰 ' + S.photo_count.toLocaleString();
    if (g && feat.length) g.innerHTML = feat.map(function (u) { return '<div class="rhrv-ph"><img src="' + esc(url(u)) + '" alt="고객 포토리뷰" loading="lazy"></div>'; }).join('');

    pages = S.pages || 1;
    // 베스트 리뷰(자동 선별 + 대표 핀) → 리스트 맨 위 섹션
    var top = S.top || [];
    if (list && top.length) {
      var best = document.createElement('div'); best.className = 'rhrv-best';
      best.innerHTML = '<div class="rhrv-best-label">베스트 리뷰</div><ul class="rhrv-list rhrv-best-list">' + top.map(item).join('') + '</ul>';
      list.parentNode.insertBefore(best, list); markLong(best);
      var lbl2 = document.createElement('div'); lbl2.className = 'rhrv-best-label'; lbl2.textContent = '전체 리뷰';
      list.parentNode.insertBefore(lbl2, list);
    }
    if (list) { list.innerHTML = (S.first || []).map(item).join(''); markLong(list); }
    // 페이지네이션(교체 방식): ‹ 1 2 3 … N › — 한 번에 20개, 페이지 이동 시 리뷰 상단으로
    if (more) more.style.display = 'none';
    var pager = document.createElement('div'); pager.className = 'rhrv-pager';
    (more ? more.parentNode : root).insertBefore(pager, more || null);
    function drawPager() {
      if (pages <= 1) { pager.innerHTML = ''; return; }
      var h = '<button class="rhrv-pg-btn" data-p="' + (page - 1) + '"' + (page <= 1 ? ' disabled' : '') + '>‹</button>';
      var win = 2, nums = [];
      for (var i = 1; i <= pages; i++) if (i === 1 || i === pages || Math.abs(i - page) <= win) nums.push(i);
      var last = 0;
      nums.forEach(function (n) {
        if (n - last > 1) h += '<span class="rhrv-pg-dots">…</span>';
        h += '<button class="rhrv-pg-btn' + (n === page ? ' on' : '') + '" data-p="' + n + '">' + n + '</button>'; last = n;
      });
      h += '<button class="rhrv-pg-btn" data-p="' + (page + 1) + '"' + (page >= pages ? ' disabled' : '') + '>›</button>';
      pager.innerHTML = h;
    }
    drawPager();
    pager.addEventListener('click', function (e) {
      var b = e.target.closest('.rhrv-pg-btn'); if (!b || b.disabled) return;
      var n = parseInt(b.getAttribute('data-p'), 10); if (!n || n === page || n < 1 || n > pages) return;
      loadPage(n).then(function (arr) {
        page = n; list.innerHTML = arr.map(item).join(''); markLong(list); drawPager();
        var lbl = root.querySelector('.rhrv-best-label:last-of-type') || list;
        (lbl || list).scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
    if (S.count > 0 && S.avg) {
      var name = (document.querySelector('meta[property="og:title"]') || {}).content || document.title;
      var ld = { '@context': 'https://schema.org', '@type': 'Product', name: name,
        aggregateRating: { '@type': 'AggregateRating', ratingValue: S.avg, reviewCount: S.count, bestRating: 5, worstRating: 1 },
        review: (S.first || []).slice(0, 5).map(function (r) { return { '@type': 'Review', reviewRating: { '@type': 'Rating', ratingValue: r.r, bestRating: 5 }, author: { '@type': 'Person', name: r.a }, datePublished: r.d, reviewBody: r.t }; }) };
      var tag = document.createElement('script'); tag.type = 'application/ld+json'; tag.textContent = JSON.stringify(ld); document.head.appendChild(tag);
    }
    root.setAttribute('data-rihoon-reviews', 'loaded:' + S.count);
    // 버전 뱃지(반영 확인용, 아주 작게)
    var vb = document.createElement('span'); vb.textContent = 'v1.4';
    vb.style.cssText = 'display:block;text-align:right;font-size:10px;color:#c9c5bf;margin-top:6px'; root.appendChild(vb);
  }).catch(function () { root.setAttribute('data-rihoon-reviews', 'error'); });
})();
