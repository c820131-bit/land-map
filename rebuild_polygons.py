# -*- coding: utf-8 -*-
import pandas as pd
import json

# 1. 매칭결과 파일 읽기
xlsx = pd.ExcelFile(r'C:\클로드\보상개발지도\중요파일\지지옥션매칭결과.xlsx')

# 2. 경공매폴리곤좌표 읽기
with open(r'C:\클로드\보상개발지도\중요파일\경공매폴리곤좌표.json', 'r', encoding='utf-8') as f:
    polygon_data = json.load(f)

print(f"폴리곤 데이터: {len(polygon_data)}개 주소")

def create_polygon_data(sheet_name, output_file):
    df = pd.read_excel(xlsx, sheet_name)
    print(f"\n{sheet_name}: {len(df)}건")

    results = []
    matched = 0

    for _, row in df.iterrows():
        addr = str(row.get('물건주소', ''))

        # 폴리곤 찾기
        polygon = None
        lat, lng = None, None

        # 정확히 일치하는 주소 찾기
        if addr in polygon_data:
            p = polygon_data[addr]
            polygon = p.get('polygon')
            lat = p.get('lat')
            lng = p.get('lng')
        else:
            # 부분 일치 시도 (앞부분만)
            addr_base = addr.split('[')[0].strip()
            for key in polygon_data:
                if key.startswith(addr_base[:20]):
                    p = polygon_data[key]
                    polygon = p.get('polygon')
                    lat = p.get('lat')
                    lng = p.get('lng')
                    break

        if polygon and len(polygon) >= 3:
            matched += 1
            results.append({
                'address': addr,
                'lat': lat,
                'lng': lng,
                'polygon': polygon,
                'case_no': str(row.get('사건번호', '-')),
                'date': str(row.get('매각날짜', '-')),
                'type': str(row.get('종류', '-')),
                'project': str(row.get('관련사업', '-')),
                'usage': str(row.get('용도', '-')),
                'area': str(row.get('면적', '-')),
                'appraisal': str(row.get('감정가', '-')),
                'min_price': str(row.get('최저가', '-')),
                'special': str(row.get('특별사항', '-'))
            })

    print(f"매칭 성공: {matched}건")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False)

    print(f"저장: {output_file}")
    return len(results)

# 완전일치
exact_count = create_polygon_data('완전일치', 'data_exact_polygons.json')

# 500m 이내
nearby_count = create_polygon_data('인근토지_500m', 'data_nearby500_polygons.json')

print(f"\n완료! 완전일치: {exact_count}개, 500m: {nearby_count}개")
