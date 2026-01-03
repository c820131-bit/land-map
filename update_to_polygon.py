# -*- coding: utf-8 -*-
import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 완전일치 로드 함수를 폴리곤 버전으로 교체
old_exact = '''var exactLoaded = false;
function loadExactMatchData(callback) {
    if (exactLoaded) { if(callback) callback(); return; }
    console.log("완전일치 데이터 로딩...");
    fetch("data_exact_match.json")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            console.log("완전일치 데이터 로드 완료:", data.length);
            data.forEach(function(d) {
                var m = createMarkerNoMap(d.lat, d.lng, '#ef4444', "exact");
                var info = createAuctionInfo(d, "완전일치");
                addClickEvent(m, info, d);
                markers.exact.push(m);
            });
            exactLoaded = true;
            document.getElementById('count-exact').textContent = data.length.toLocaleString();
            if(callback) callback();
        });
}'''

new_exact = '''var exactLoaded = false;
var polygons = { exact: [], nearby500: [] };
function loadExactMatchData(callback) {
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
                    strokeWeight: 2,
                    strokeColor: '#10b981',
                    strokeOpacity: 0.8,
                    fillColor: '#10b981',
                    fillOpacity: 0.4
                });
                kakao.maps.event.addListener(poly, 'click', function() {
                    var info = '<div style="padding:12px;background:#1a1a1f;color:#fff;border-radius:8px;font-size:12px;max-width:300px">' +
                        '<div style="font-weight:600;color:#10b981;margin-bottom:8px">완전일치</div>' +
                        '<div>' + (d.address || '-') + '</div>' +
                        '<div style="margin-top:6px;color:#94a3b8">사건번호: ' + (d.case_no || '-') + '</div>' +
                        '</div>';
                    var iw = new kakao.maps.InfoWindow({ content: info });
                    iw.open(map, new kakao.maps.LatLng(d.lat, d.lng));
                    setTimeout(function() { iw.close(); }, 5000);
                });
                polygons.exact.push(poly);
            });
            exactLoaded = true;
            document.getElementById('count-exact').textContent = data.length.toLocaleString();
            if(callback) callback();
        });
}'''

html = html.replace(old_exact, new_exact)

# 2. 500m 이내 로드 함수도 폴리곤 버전으로 교체
old_500 = '''var nearby500Loaded = false;
function loadNearby500Data(callback) {
    if (nearby500Loaded) { if(callback) callback(); return; }
    console.log("500m 이내 데이터 로딩...");
    fetch("data_nearby_500m.json")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            console.log("500m 이내 데이터 로드 완료:", data.length);
            data.forEach(function(d) {
                var m = createMarkerNoMap(d.lat, d.lng, '#fbbf24', "nearby500");
                var info = createAuctionInfo(d, "500m 이내");
                addClickEvent(m, info, d);
                markers.nearby500.push(m);
            });
            nearby500Loaded = true;
            document.getElementById('count-nearby500').textContent = data.length.toLocaleString();
            if(callback) callback();
        });
}'''

new_500 = '''var nearby500Loaded = false;
function loadNearby500Data(callback) {
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
                    strokeWeight: 2,
                    strokeColor: '#fbbf24',
                    strokeOpacity: 0.8,
                    fillColor: '#fbbf24',
                    fillOpacity: 0.4
                });
                kakao.maps.event.addListener(poly, 'click', function() {
                    var info = '<div style="padding:12px;background:#1a1a1f;color:#fff;border-radius:8px;font-size:12px;max-width:300px">' +
                        '<div style="font-weight:600;color:#fbbf24;margin-bottom:8px">500m 이내</div>' +
                        '<div>' + (d.address || '-') + '</div>' +
                        '<div style="margin-top:6px;color:#94a3b8">사건번호: ' + (d.case_no || '-') + '</div>' +
                        '</div>';
                    var iw = new kakao.maps.InfoWindow({ content: info });
                    iw.open(map, new kakao.maps.LatLng(d.lat, d.lng));
                    setTimeout(function() { iw.close(); }, 5000);
                });
                polygons.nearby500.push(poly);
            });
            nearby500Loaded = true;
            document.getElementById('count-nearby500').textContent = data.length.toLocaleString();
            if(callback) callback();
        });
}'''

html = html.replace(old_500, new_500)

# 3. toggleLayer에서 마커 대신 폴리곤 표시/숨김
old_toggle_exact = '''if (category === 'exact' && show && !exactLoaded) {
        loadExactMatchData(function() {
            markers.exact.forEach(function(m) { m.setMap(map); });
        });
        return;
    }
    if (category === 'exact' && exactLoaded) {
        markers.exact.forEach(function(m) { m.setMap(show ? map : null); });
        return;
    }'''

new_toggle_exact = '''if (category === 'exact' && show && !exactLoaded) {
        loadExactMatchData(function() {
            polygons.exact.forEach(function(p) { p.setMap(map); });
        });
        return;
    }
    if (category === 'exact' && exactLoaded) {
        polygons.exact.forEach(function(p) { p.setMap(show ? map : null); });
        return;
    }'''

html = html.replace(old_toggle_exact, new_toggle_exact)

old_toggle_500 = '''if (category === 'nearby500' && show && !nearby500Loaded) {
        loadNearby500Data(function() {
            markers.nearby500.forEach(function(m) { m.setMap(map); });
        });
        return;
    }
    if (category === 'nearby500' && nearby500Loaded) {
        markers.nearby500.forEach(function(m) { m.setMap(show ? map : null); });
        return;
    }'''

new_toggle_500 = '''if (category === 'nearby500' && show && !nearby500Loaded) {
        loadNearby500Data(function() {
            polygons.nearby500.forEach(function(p) { p.setMap(map); });
        });
        return;
    }
    if (category === 'nearby500' && nearby500Loaded) {
        polygons.nearby500.forEach(function(p) { p.setMap(show ? map : null); });
        return;
    }'''

html = html.replace(old_toggle_500, new_toggle_500)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("index.html 폴리곤 버전으로 수정 완료!")
