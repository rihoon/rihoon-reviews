# -*- coding: utf-8 -*-
"""스마트스토어 리뷰 스크랩 POC: 실제 브라우저로 상품페이지 열고 리뷰 API 응답을 가로채 구조 확인."""
import sys, json, asyncio
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

PRODUCT = sys.argv[1] if len(sys.argv) > 1 else '11001787369'
URL = f'https://smartstore.naver.com/main/products/{PRODUCT}'

async def main():
    captured = []
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        # 대표 승인(2026-08-18): 기존 CS자동화 네이버 세션 재사용(읽기 전용)
        SESSION = r'Z:\rihoon1\자동화\리훈_CS자동화\session.json'
        ctx = await b.new_context(storage_state=SESSION,
                                  user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36',
                                  locale='ko-KR')
        page = await ctx.new_page()
        async def on_resp(resp):
            u = resp.url
            if 'review' in u.lower() and resp.status == 200:
                try:
                    j = await resp.json()
                    captured.append((u, j))
                except Exception:
                    pass
        page.on('response', on_resp)
        await page.goto(URL, wait_until='domcontentloaded', timeout=45000)
        await page.wait_for_timeout(4000)
        # 리뷰 탭까지 스크롤해서 리뷰 API 유발
        for _ in range(6):
            await page.mouse.wheel(0, 1500); await page.wait_for_timeout(700)
        await page.wait_for_timeout(2500)
        print('page title:', await page.title())
        await b.close()

    print(f'\ncaptured review responses: {len(captured)}')
    for u, j in captured[:3]:
        print('\n== URL:', u[:140])
        s = json.dumps(j, ensure_ascii=False)
        print('keys:', list(j.keys())[:15] if isinstance(j, dict) else type(j))
        print(s[:1500])
    # 저장
    json.dump([{'url':u,'body':j} for u,j in captured], open('_probe_reviews.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)

asyncio.run(main())
