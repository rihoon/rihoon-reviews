# -*- coding: utf-8 -*-
"""네이버 커머스 API로 리뷰 조회 지원 여부 실측. 리훈 문의함 .env.local의 COMMERCE_CLIENT_ID/SECRET 사용(bcrypt 서명 → client_credentials)."""
import sys, time, base64, json, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
import bcrypt

ENV = r'Z:\rihoon1\자동화\리훈 문의함\rihoon-inbox\.env.local'
env = {}
for line in open(ENV, encoding='utf-8'):
    line=line.strip()
    if line and not line.startswith('#') and '=' in line:
        k,v=line.split('=',1); env[k.strip()]=v.strip().strip('"').strip("'")
CID, CSEC = env['COMMERCE_CLIENT_ID'], env['COMMERCE_CLIENT_SECRET']

ts = int(time.time()*1000)
sign = base64.b64encode(bcrypt.hashpw(f'{CID}_{ts}'.encode(), CSEC.encode())).decode()
body = urllib.parse.urlencode({'client_id':CID,'timestamp':str(ts),'client_secret_sign':sign,'grant_type':'client_credentials','type':'SELF'}).encode()
req = urllib.request.Request('https://api.commerce.naver.com/external/v1/oauth2/token', data=body, headers={'Content-Type':'application/x-www-form-urlencoded'})
tok = json.loads(urllib.request.urlopen(req, timeout=20).read())['access_token']
print('token OK')

H={'Authorization':f'Bearer {tok}'}
def hit(path):
    url='https://api.commerce.naver.com/external'+path
    r=urllib.request.Request(url, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            b=resp.read().decode(); print(f'[{resp.status}] {path}'); print('   ', b[:400]); return b
    except urllib.error.HTTPError as e:
        print(f'[{e.code}] {path}'); print('   ', e.read().decode(errors="replace")[:300])

# 리뷰 엔드포인트 후보 (v1/v2, 다양한 표기)
for p in [
    '/v1/contents/reviews?page=1&size=5',
    '/v1/contents/reviews/query?page=1&size=5',
    '/v1/reviews?page=1&size=5',
    '/v1/products/reviews?page=1&size=5',
    '/v2/contents/reviews?page=1&size=5',
    '/v1/contents/reviews/product-reviews?page=1&size=5',
]:
    hit(p)
