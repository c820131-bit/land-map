import re
import json

# 기존 index.html에서 데이터 추출
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 데이터 변수 추출
data_vars = {}
for var_name in ['inside', 'nearby', 'auction_data', 'public_data', 'projData', 'railData', 'highwayData', 'devData']:
    pattern = rf'var {var_name}=(\[.*?\]);'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        try:
            data_vars[var_name] = json.loads(match.group(1))
            print(f"{var_name}: {len(data_vars[var_name])}건")
        except:
            print(f"{var_name}: 파싱 실패")

# 통계
total_auction = len(data_vars.get('inside', [])) + len(data_vars.get('nearby', [])) + len(data_vars.get('auction_data', [])) + len(data_vars.get('public_data', []))
print(f"\n총 경공매: {total_auction}건")
print(f"- 지구내: {len(data_vars.get('inside', []))}건")
print(f"- 근처: {len(data_vars.get('nearby', []))}건")
print(f"- 경매: {len(data_vars.get('auction_data', []))}건")
print(f"- 공매: {len(data_vars.get('public_data', []))}건")
