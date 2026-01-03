# -*- coding: utf-8 -*-
# 폴리곤 + 마커 함께 표시 (축소해도 마커가 보임)

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 완전일치 - 폴리곤 + 마커 함께 표시
old_exact = '''function loadExactMatchData(callback) {
    if (exactLoaded) { if(callback) callback(); return; }
    console.log("완전일치 폴리곤 데이터 로딩...");
    fetch("data_exact_polygons.json")'''

new_exact = '''function loadExactMatchData(callback) {
    if (exactLoaded) { if(callback) callback(); return; }
    console.log("완전일치 폴리곤 데이터 로딩...");

    // 완전일치 마커 이미지
    var exactMarkerImg = new kakao.maps.MarkerImage(
        'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/marker_red.png',
        new kakao.maps.Size(35, 40),
        { offset: new kakao.maps.Point(17, 40) }
    );

    fetch("data_exact_polygons.json")'''

html = html.replace(old_exact, new_exact)

# polygons.exact.push(poly) 앞에 마커 추가
old_push_exact = '''                polygons.exact.push(poly);
            });
            exactLoaded = true;
            document.getElementById('count-exact').textContent = data.length.toLocaleString();'''

new_push_exact = '''                // 마커도 함께 추가 (축소해도 보이게)
                var marker = new kakao.maps.Marker({
                    position: new kakao.maps.LatLng(d.lat, d.lng),
                    clickable: true
                });
                kakao.maps.event.addListener(marker, 'click', function() {
                    var content = '<div style="padding:16px;background:#1f2937;color:#fff;border-radius:12px;font-size:13px;max-width:400px;border:3px solid #10b981;box-shadow:0 8px 30px rgba(0,0,0,0.6)">' +
                        '<div style="font-weight:700;color:#10b981;margin-bottom:12px;font-size:17px;border-bottom:2px solid #374151;padding-bottom:10px">✅ 완전일치 경매물건</div>' +
                        '<div style="margin-bottom:12px;font-weight:600;font-size:14px">' + (d.address || '-') + '</div>' +
                        '<table style="width:100%;font-size:13px;color:#e5e7eb">' +
                        '<tr><td style="padding:6px 0;color:#9ca3af;width:80px">사건번호</td><td style="padding:6px 0;font-weight:500">' + (d.case_no || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">매각일</td><td style="padding:6px 0">' + (d.date || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">종류</td><td style="padding:6px 0">' + (d.type || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">관련사업</td><td style="padding:6px 0;word-break:break-all">' + (d.project || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">용도</td><td style="padding:6px 0">' + (d.usage || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">면적</td><td style="padding:6px 0">' + (d.area || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">감정가</td><td style="padding:6px 0;color:#fbbf24;font-weight:700;font-size:14px">' + (d.appraisal && d.appraisal !== 'nan' ? Number(d.appraisal).toLocaleString() + '원' : '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">최저가</td><td style="padding:6px 0;color:#ef4444;font-weight:700;font-size:14px">' + (d.min_price && d.min_price !== 'nan' ? Number(d.min_price).toLocaleString() + '원' : '-') + '</td></tr>' +
                        '</table></div>';
                    var overlay = new kakao.maps.CustomOverlay({ content: content, position: marker.getPosition(), yAnchor: 1.2 });
                    overlay.setMap(map);
                    setTimeout(function() { overlay.setMap(null); }, 12000);
                });
                markers.exact.push(marker);
                polygons.exact.push(poly);
            });
            exactLoaded = true;
            document.getElementById('count-exact').textContent = data.length.toLocaleString();'''

html = html.replace(old_push_exact, new_push_exact)

# 500m도 마커 추가
old_500 = '''function loadNearby500Data(callback) {
    if (nearby500Loaded) { if(callback) callback(); return; }
    console.log("500m 이내 폴리곤 데이터 로딩...");
    fetch("data_nearby500_polygons.json")'''

new_500 = '''function loadNearby500Data(callback) {
    if (nearby500Loaded) { if(callback) callback(); return; }
    console.log("500m 이내 폴리곤 데이터 로딩...");

    fetch("data_nearby500_polygons.json")'''

html = html.replace(old_500, new_500)

old_push_500 = '''                polygons.nearby500.push(poly);
            });
            nearby500Loaded = true;
            document.getElementById('count-nearby500').textContent = data.length.toLocaleString();'''

new_push_500 = '''                // 마커도 함께 추가 (축소해도 보이게)
                var marker = new kakao.maps.Marker({
                    position: new kakao.maps.LatLng(d.lat, d.lng),
                    clickable: true
                });
                kakao.maps.event.addListener(marker, 'click', function() {
                    var content = '<div style="padding:16px;background:#1f2937;color:#fff;border-radius:12px;font-size:13px;max-width:400px;border:3px solid #fbbf24;box-shadow:0 8px 30px rgba(0,0,0,0.6)">' +
                        '<div style="font-weight:700;color:#fbbf24;margin-bottom:12px;font-size:17px;border-bottom:2px solid #374151;padding-bottom:10px">📍 500m 이내 경매물건</div>' +
                        '<div style="margin-bottom:12px;font-weight:600;font-size:14px">' + (d.address || '-') + '</div>' +
                        '<table style="width:100%;font-size:13px;color:#e5e7eb">' +
                        '<tr><td style="padding:6px 0;color:#9ca3af;width:80px">사건번호</td><td style="padding:6px 0;font-weight:500">' + (d.case_no || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">매각일</td><td style="padding:6px 0">' + (d.date || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">종류</td><td style="padding:6px 0">' + (d.type || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">관련사업</td><td style="padding:6px 0;word-break:break-all">' + (d.project || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">용도</td><td style="padding:6px 0">' + (d.usage || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">면적</td><td style="padding:6px 0">' + (d.area || '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">감정가</td><td style="padding:6px 0;color:#fbbf24;font-weight:700;font-size:14px">' + (d.appraisal && d.appraisal !== 'nan' ? Number(d.appraisal).toLocaleString() + '원' : '-') + '</td></tr>' +
                        '<tr><td style="padding:6px 0;color:#9ca3af">최저가</td><td style="padding:6px 0;color:#ef4444;font-weight:700;font-size:14px">' + (d.min_price && d.min_price !== 'nan' ? Number(d.min_price).toLocaleString() + '원' : '-') + '</td></tr>' +
                        '</table></div>';
                    var overlay = new kakao.maps.CustomOverlay({ content: content, position: marker.getPosition(), yAnchor: 1.2 });
                    overlay.setMap(map);
                    setTimeout(function() { overlay.setMap(null); }, 12000);
                });
                markers.nearby500.push(marker);
                polygons.nearby500.push(poly);
            });
            nearby500Loaded = true;
            document.getElementById('count-nearby500').textContent = data.length.toLocaleString();'''

html = html.replace(old_push_500, new_push_500)

# toggleLayer에서 마커도 함께 표시/숨김
old_toggle = '''    // 완전일치/500m는 polygons 사용
    if (category === 'exact' && exactLoaded) {
        polygons.exact.forEach(function(p) { p.setMap(show ? map : null); });
        return;
    }
    if (category === 'nearby500' && nearby500Loaded) {
        polygons.nearby500.forEach(function(p) { p.setMap(show ? map : null); });
        return;
    }'''

new_toggle = '''    // 완전일치/500m는 polygons + markers 함께 사용
    if (category === 'exact' && exactLoaded) {
        polygons.exact.forEach(function(p) { p.setMap(show ? map : null); });
        markers.exact.forEach(function(m) { m.setMap(show ? map : null); });
        return;
    }
    if (category === 'nearby500' && nearby500Loaded) {
        polygons.nearby500.forEach(function(p) { p.setMap(show ? map : null); });
        markers.nearby500.forEach(function(m) { m.setMap(show ? map : null); });
        return;
    }'''

html = html.replace(old_toggle, new_toggle)

# 로드 후 마커도 표시
old_load_exact = '''        loadExactMatchData(function() {
            polygons.exact.forEach(function(p) { p.setMap(map); });
        });'''

new_load_exact = '''        loadExactMatchData(function() {
            polygons.exact.forEach(function(p) { p.setMap(map); });
            markers.exact.forEach(function(m) { m.setMap(map); });
        });'''

html = html.replace(old_load_exact, new_load_exact)

old_load_500 = '''        loadNearby500Data(function() {
            polygons.nearby500.forEach(function(p) { p.setMap(map); });
        });'''

new_load_500 = '''        loadNearby500Data(function() {
            polygons.nearby500.forEach(function(p) { p.setMap(map); });
            markers.nearby500.forEach(function(m) { m.setMap(map); });
        });'''

html = html.replace(old_load_500, new_load_500)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("폴리곤 + 마커 표시 수정 완료!")
