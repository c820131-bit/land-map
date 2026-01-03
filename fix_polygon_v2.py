# -*- coding: utf-8 -*-
import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 완전일치 로드 함수 전체 교체
old_exact_func = '''function loadExactMatchData(callback) {
    if (exactLoaded) { if(callback) callback(); return; }
    console.log("완전일치 폴리곤 데이터 로딩...");
    fetch("data_exact_polygons.json")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            console.log("완전일치 폴리곤 로드 완료:", data.length);
            data.forEach(function(d) {
                if (!d.polygon || d.polygon.length < 3) return;
                var path = d.polygon.map(function(c) {
                    return new kakao.maps.LatLng(c[1], c[0]);
                });
                var poly = new kakao.maps.Polygon({
                    path: path,
                    strokeWeight: 3,
                    strokeColor: '#10b981',
                    strokeOpacity: 1,
                    fillColor: '#10b981',
                    fillOpacity: 0.5
                });
                kakao.maps.event.addListener(poly, 'click', function() {
                    var info = '<div style="padding:14px;background:#1a1a1f;color:#fff;border-radius:10px;font-size:12px;max-width:350px;border:1px solid #10b981">' +
                        '<div style="font-weight:700;color:#10b981;margin-bottom:10px;font-size:14px">완전일치</div>' +
                        '<div style="margin-bottom:6px">' + (d.address || '-') + '</div>' +
                        '<div style="color:#94a3b8;font-size:11px;line-height:1.6">' +
                        '사건번호: ' + (d.case_no || '-') + '<br>' +
                        '매각일: ' + (d.date || '-') + '<br>' +
                        '종류: ' + (d.type || '-') + '<br>' +
                        '관련사업: ' + (d.project || '-') + '<br>' +
                        '용도: ' + (d.usage || '-') + '<br>' +
                        '면적: ' + (d.area || '-') + '<br>' +
                        '감정가: ' + (d.appraisal ? Number(d.appraisal).toLocaleString() + '원' : '-') + '<br>' +
                        '최저가: ' + (d.min_price ? Number(d.min_price).toLocaleString() + '원' : '-') +
                        '</div></div>';
                    var iw = new kakao.maps.InfoWindow({ content: info });
                    iw.open(map, new kakao.maps.LatLng(d.lat, d.lng));
                    setTimeout(function() { iw.close(); }, 8000);
                });
                polygons.exact.push(poly);
            });
            exactLoaded = true;
            document.getElementById('count-exact').textContent = data.length.toLocaleString();
            if(callback) callback();
        });
}'''

new_exact_func = '''function loadExactMatchData(callback) {
    if (exactLoaded) { if(callback) callback(); return; }
    console.log("완전일치 폴리곤 데이터 로딩...");
    fetch("data_exact_polygons.json")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            console.log("완전일치 폴리곤 로드 완료:", data.length);
            data.forEach(function(d) {
                if (!d.polygon || d.polygon.length < 3) return;
                var path = d.polygon.map(function(c) {
                    return new kakao.maps.LatLng(c[1], c[0]);
                });
                var poly = new kakao.maps.Polygon({
                    path: path,
                    strokeWeight: 5,
                    strokeColor: '#10b981',
                    strokeOpacity: 1,
                    fillColor: '#10b981',
                    fillOpacity: 0.65
                });
                kakao.maps.event.addListener(poly, 'mouseover', function() {
                    poly.setOptions({ fillOpacity: 0.85, strokeWeight: 7 });
                });
                kakao.maps.event.addListener(poly, 'mouseout', function() {
                    poly.setOptions({ fillOpacity: 0.65, strokeWeight: 5 });
                });
                kakao.maps.event.addListener(poly, 'click', function(mouseEvent) {
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
                    var overlay = new kakao.maps.CustomOverlay({ content: content, position: mouseEvent.latLng, yAnchor: 1.2 });
                    overlay.setMap(map);
                    setTimeout(function() { overlay.setMap(null); }, 12000);
                });
                polygons.exact.push(poly);
            });
            exactLoaded = true;
            document.getElementById('count-exact').textContent = data.length.toLocaleString();
            if(callback) callback();
        });
}'''

if old_exact_func in html:
    html = html.replace(old_exact_func, new_exact_func)
    print("완전일치 함수 교체 성공")
else:
    print("완전일치 함수 패턴 못찾음")

# 500m 함수도 교체
old_500_func = '''function loadNearby500Data(callback) {
    if (nearby500Loaded) { if(callback) callback(); return; }
    console.log("500m 이내 폴리곤 데이터 로딩...");
    fetch("data_nearby500_polygons.json")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            console.log("500m 이내 폴리곤 로드 완료:", data.length);
            data.forEach(function(d) {
                if (!d.polygon || d.polygon.length < 3) return;
                var path = d.polygon.map(function(c) {
                    return new kakao.maps.LatLng(c[1], c[0]);
                });
                var poly = new kakao.maps.Polygon({
                    path: path,
                    strokeWeight: 3,
                    strokeColor: '#fbbf24',
                    strokeOpacity: 1,
                    fillColor: '#fbbf24',
                    fillOpacity: 0.5
                });
                kakao.maps.event.addListener(poly, 'click', function() {
                    var info = '<div style="padding:14px;background:#1a1a1f;color:#fff;border-radius:10px;font-size:12px;max-width:350px;border:1px solid #fbbf24">' +
                        '<div style="font-weight:700;color:#fbbf24;margin-bottom:10px;font-size:14px">500m 이내</div>' +
                        '<div style="margin-bottom:6px">' + (d.address || '-') + '</div>' +
                        '<div style="color:#94a3b8;font-size:11px;line-height:1.6">' +
                        '사건번호: ' + (d.case_no || '-') + '<br>' +
                        '매각일: ' + (d.date || '-') + '<br>' +
                        '종류: ' + (d.type || '-') + '<br>' +
                        '관련사업: ' + (d.project || '-') + '<br>' +
                        '용도: ' + (d.usage || '-') + '<br>' +
                        '면적: ' + (d.area || '-') + '<br>' +
                        '감정가: ' + (d.appraisal ? Number(d.appraisal).toLocaleString() + '원' : '-') + '<br>' +
                        '최저가: ' + (d.min_price ? Number(d.min_price).toLocaleString() + '원' : '-') +
                        '</div></div>';
                    var iw = new kakao.maps.InfoWindow({ content: info });
                    iw.open(map, new kakao.maps.LatLng(d.lat, d.lng));
                    setTimeout(function() { iw.close(); }, 8000);
                });
                polygons.nearby500.push(poly);
            });
            nearby500Loaded = true;
            document.getElementById('count-nearby500').textContent = data.length.toLocaleString();
            if(callback) callback();
        });
}'''

new_500_func = '''function loadNearby500Data(callback) {
    if (nearby500Loaded) { if(callback) callback(); return; }
    console.log("500m 이내 폴리곤 데이터 로딩...");
    fetch("data_nearby500_polygons.json")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            console.log("500m 이내 폴리곤 로드 완료:", data.length);
            data.forEach(function(d) {
                if (!d.polygon || d.polygon.length < 3) return;
                var path = d.polygon.map(function(c) {
                    return new kakao.maps.LatLng(c[1], c[0]);
                });
                var poly = new kakao.maps.Polygon({
                    path: path,
                    strokeWeight: 5,
                    strokeColor: '#fbbf24',
                    strokeOpacity: 1,
                    fillColor: '#fbbf24',
                    fillOpacity: 0.65
                });
                kakao.maps.event.addListener(poly, 'mouseover', function() {
                    poly.setOptions({ fillOpacity: 0.85, strokeWeight: 7 });
                });
                kakao.maps.event.addListener(poly, 'mouseout', function() {
                    poly.setOptions({ fillOpacity: 0.65, strokeWeight: 5 });
                });
                kakao.maps.event.addListener(poly, 'click', function(mouseEvent) {
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
                    var overlay = new kakao.maps.CustomOverlay({ content: content, position: mouseEvent.latLng, yAnchor: 1.2 });
                    overlay.setMap(map);
                    setTimeout(function() { overlay.setMap(null); }, 12000);
                });
                polygons.nearby500.push(poly);
            });
            nearby500Loaded = true;
            document.getElementById('count-nearby500').textContent = data.length.toLocaleString();
            if(callback) callback();
        });
}'''

if old_500_func in html:
    html = html.replace(old_500_func, new_500_func)
    print("500m 함수 교체 성공")
else:
    print("500m 함수 패턴 못찾음")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("저장 완료!")
