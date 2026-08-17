/* 리훈 리뷰 위젯 v1 — 격리 저장소(JSON) → skin41 .rh-review-mock 채우기 + JSON-LD.
 * 안전원칙: cafe24 상품후기 게시판/상세설명/EP 무접촉. 오직 별도 fetch → 프론트 렌더.
 * 사용: <script src=".../rihoon-reviews.js" data-base="https://<host>/data"></script>
 */
(function () {
  var s = document.currentScript;
  var BASE = (s && s.getAttribute('data-base')) || '';
  var m = location.search.match(/product_no=(\d+)/);
  var PNO = (s && s.getAttribute('data-product')) || (m && m[1]);
  if (!PNO || !BASE) return;

  var root = document.querySelector('.rh-review-mock');
  if (!root) return;

  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function stars(n) { n = Math.round(n || 0); return '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n); }
  function fdate(d) { return (d || '').replace(/-/g, '.'); }
  function item(r) {
    return '<li class="rhrv-item"><div class="rhrv-meta"><span class="rhrv-st">' + stars(r.r) +
      '</span><span class="rhrv-name">' + esc(r.a) + '</span><span class="rhrv-date">' + fdate(r.d) +
      '</span></div><p class="rhrv-text">' + esc(r.t).replace(/\n/g, '<br>') + '</p></li>';
  }

  var list = root.querySelector('.rhrv-list');
  var more = root.querySelector('.rhrv-more');
  var page = 1, pages = 1;

  function loadPage(n) {
    return fetch(BASE + '/' + PNO + '/p' + n + '.json').then(function (r) { return r.json(); });
  }

  fetch(BASE + '/' + PNO + '/summary.json').then(function (r) { return r.json(); }).then(function (S) {
    // 헤더
    var sc = root.querySelector('.rhrv-score'); if (sc) sc.textContent = (S.avg || 0).toFixed(1);
    var st = root.querySelector('.rhrv-stars'); if (st) st.textContent = stars(S.avg);
    var tot = root.querySelector('.rhrv-total b'); if (tot) tot.textContent = S.count.toLocaleString();
    // 포토 없음(v1) → 갤러리 숨김
    var g = root.querySelector('.rhrv-gallery-wrap'); if (g) g.style.display = 'none';
    // 리스트
    pages = S.pages || 1;
    if (list) list.innerHTML = (S.first || []).map(item).join('');
    if (more) {
      more.style.display = pages > 1 ? '' : 'none';
      more.addEventListener('click', function () {
        if (page >= pages) return;
        page++;
        loadPage(page).then(function (arr) {
          list.insertAdjacentHTML('beforeend', arr.map(item).join(''));
          if (page >= pages) more.style.display = 'none';
        });
      });
    }
    // JSON-LD (구글용) — 페이지에 실제로 렌더된 리뷰가 있을 때만 심음(정책 일치)
    if (S.count > 0 && S.avg) {
      var name = (document.querySelector('meta[property="og:title"]') || {}).content || document.title;
      var ld = {
        '@context': 'https://schema.org', '@type': 'Product', name: name,
        aggregateRating: { '@type': 'AggregateRating', ratingValue: S.avg, reviewCount: S.count, bestRating: 5, worstRating: 1 },
        review: (S.first || []).slice(0, 5).map(function (r) {
          return { '@type': 'Review', reviewRating: { '@type': 'Rating', ratingValue: r.r, bestRating: 5 },
                   author: { '@type': 'Person', name: r.a }, datePublished: r.d, reviewBody: r.t };
        })
      };
      var tag = document.createElement('script'); tag.type = 'application/ld+json';
      tag.textContent = JSON.stringify(ld); document.head.appendChild(tag);
    }
    root.setAttribute('data-rihoon-reviews', 'loaded:' + S.count);
  }).catch(function (e) { root.setAttribute('data-rihoon-reviews', 'error'); });
})();
