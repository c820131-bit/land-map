import re
import json
import subprocess

result = subprocess.run(['git', 'show', '867e827:index.html'], capture_output=True, text=True, encoding='utf-8')
content = result.stdout

data_vars = {}
for var_name in ['inside', 'nearby', 'auction_data', 'public_data', 'projData', 'railData', 'highwayData']:
    pattern = rf'var {var_name}=(\[.*?\]);'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        try:
            data_vars[var_name] = json.loads(match.group(1))
        except:
            data_vars[var_name] = []

inside_json = json.dumps(data_vars.get('inside', []), ensure_ascii=False)
nearby_json = json.dumps(data_vars.get('nearby', []), ensure_ascii=False)
auction_json = json.dumps(data_vars.get('auction_data', []), ensure_ascii=False)
public_json = json.dumps(data_vars.get('public_data', []), ensure_ascii=False)
proj_json = json.dumps(data_vars.get('projData', []), ensure_ascii=False)
rail_json = json.dumps(data_vars.get('railData', []), ensure_ascii=False)
highway_json = json.dumps(data_vars.get('highwayData', []), ensure_ascii=False)

cnt_inside = len(data_vars.get('inside', []))
cnt_nearby = len(data_vars.get('nearby', []))
cnt_auction = len(data_vars.get('auction_data', []))
cnt_public = len(data_vars.get('public_data', []))
cnt_proj = len(data_vars.get('projData', []))
cnt_rail = len(data_vars.get('railData', []))
cnt_highway = len(data_vars.get('highwayData', []))
cnt_total = cnt_inside + cnt_nearby + cnt_auction + cnt_public

html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>투자맵 프로토타입 - 5개 레이어</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey=7e60f6a42602355b925c66ea6db3bd87"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Malgun Gothic', sans-serif;
            overflow: hidden;
        }}

        #map {{
            width: 100vw;
            height: 100vh;
        }}

        /* 컨트롤 패널 */
        .control-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 20px;
            min-width: 280px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 100;
        }}

        .panel-header {{
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}

        .layer-group {{
            margin-bottom: 15px;
        }}

        .layer-title {{
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #555;
        }}

        .layer-item {{
            display: flex;
            align-items: center;
            padding: 8px;
            margin-bottom: 5px;
            background: #f8f9fa;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .layer-item:hover {{
            background: #e9ecef;
            transform: translateX(3px);
        }}

        .layer-item input[type="checkbox"] {{
            margin-right: 10px;
            width: 18px;
            height: 18px;
            cursor: pointer;
        }}

        .layer-color {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 8px;
            border: 2px solid #fff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }}

        .layer-name {{
            flex: 1;
            font-size: 13px;
        }}

        .layer-count {{
            font-size: 11px;
            color: #666;
            background: #fff;
            padding: 2px 8px;
            border-radius: 10px;
        }}

        /* 통계 패널 */
        .stats-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 20px;
            min-width: 220px;
            z-index: 100;
        }}

        .stats-title {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 12px;
            color: #333;
        }}

        .stat-item {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #eee;
        }}

        .stat-item:last-child {{
            border-bottom: none;
        }}

        .stat-label {{
            font-size: 13px;
            color: #666;
        }}

        .stat-value {{
            font-size: 14px;
            font-weight: bold;
            color: #4CAF50;
        }}

        /* 인포윈도우 커스텀 */
        .custom-info {{
            padding: 12px;
            min-width: 200px;
        }}

        .info-title {{
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
        }}

        .info-content {{
            font-size: 12px;
            color: #666;
            line-height: 1.6;
        }}

        .info-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 4px 2px 0 0;
        }}

        /* 범례 */
        .legend {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 12px;
            z-index: 100;
        }}

        .legend-title {{
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 8px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 4px;
            font-size: 11px;
        }}

        .legend-item span:first-child {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 6px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>

    <!-- 컨트롤 패널 -->
    <div class="control-panel">
        <div class="panel-header">🗺️ 투자맵 레이어</div>

        <div class="layer-group">
            <div class="layer-title">🚇 교통 인프라</div>
            <div class="layer-item" onclick="toggleLayer('railway')">
                <input type="checkbox" id="layer-railway" checked>
                <div class="layer-color" style="background: #2196F3;"></div>
                <span class="layer-name">철도예정지</span>
                <span class="layer-count" id="count-railway">{cnt_rail}</span>
            </div>
            <div class="layer-item" onclick="toggleLayer('ic')">
                <input type="checkbox" id="layer-ic" checked>
                <div class="layer-color" style="background: #FF9800;"></div>
                <span class="layer-name">IC진출입로</span>
                <span class="layer-count" id="count-ic">{cnt_highway}</span>
            </div>
            <div class="layer-item" onclick="toggleLayer('highway')">
                <input type="checkbox" id="layer-highway" checked>
                <div class="layer-color" style="background: #9C27B0;"></div>
                <span class="layer-name">고속도로</span>
                <span class="layer-count" id="count-highway">{cnt_highway}</span>
            </div>
        </div>

        <div class="layer-group">
            <div class="layer-title">🏗️ 개발 & 투자</div>
            <div class="layer-item" onclick="toggleLayer('development')">
                <input type="checkbox" id="layer-development" checked>
                <div class="layer-color" style="background: #4CAF50;"></div>
                <span class="layer-name">개발예정지</span>
                <span class="layer-count" id="count-development">{cnt_proj}</span>
            </div>
            <div class="layer-item" onclick="toggleLayer('inside')">
                <input type="checkbox" id="layer-inside" checked>
                <div class="layer-color" style="background: #E91E63;"></div>
                <span class="layer-name">지구내 경공매</span>
                <span class="layer-count" id="count-inside">{cnt_inside}</span>
            </div>
            <div class="layer-item" onclick="toggleLayer('nearby')">
                <input type="checkbox" id="layer-nearby" checked>
                <div class="layer-color" style="background: #FF5722;"></div>
                <span class="layer-name">지구인근 경공매</span>
                <span class="layer-count" id="count-nearby">{cnt_nearby}</span>
            </div>
            <div class="layer-item" onclick="toggleLayer('auction')">
                <input type="checkbox" id="layer-auction">
                <div class="layer-color" style="background: #F44336;"></div>
                <span class="layer-name">경매</span>
                <span class="layer-count" id="count-auction">{cnt_auction}</span>
            </div>
            <div class="layer-item" onclick="toggleLayer('public')">
                <input type="checkbox" id="layer-public">
                <div class="layer-color" style="background: #9C27B0;"></div>
                <span class="layer-name">공매</span>
                <span class="layer-count" id="count-public">{cnt_public}</span>
            </div>
            <div class="layer-item" onclick="toggleLayer('land')">
                <input type="checkbox" id="layer-land">
                <div class="layer-color" style="background: rgba(76, 175, 80, 0.3); border: 2px solid #4CAF50;"></div>
                <span class="layer-name">토지보상구역</span>
                <span class="layer-count" id="count-land">{cnt_proj}</span>
            </div>
        </div>
    </div>

    <!-- 통계 패널 -->
    <div class="stats-panel">
        <div class="stats-title">📊 데이터 통계</div>
        <div class="stat-item">
            <span class="stat-label">전체 항목</span>
            <span class="stat-value" id="total-count">{cnt_total}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">표시 중</span>
            <span class="stat-value" id="visible-count">{cnt_inside + cnt_nearby}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">선택됨</span>
            <span class="stat-value" id="selected-count">0</span>
        </div>
    </div>

    <!-- 범례 -->
    <div class="legend">
        <div class="legend-title">💡 범례</div>
        <div class="legend-item">
            <span style="background: #2196F3;"></span>
            <span>철도역</span>
        </div>
        <div class="legend-item">
            <span style="background: #FF9800;"></span>
            <span>IC</span>
        </div>
        <div class="legend-item">
            <span style="background: #9C27B0;"></span>
            <span>고속도로</span>
        </div>
        <div class="legend-item">
            <span style="background: #4CAF50;"></span>
            <span>개발지</span>
        </div>
        <div class="legend-item">
            <span style="background: #E91E63;"></span>
            <span>지구내</span>
        </div>
        <div class="legend-item">
            <span style="background: #FF5722;"></span>
            <span>지구인근</span>
        </div>
        <div class="legend-item">
            <span style="background: #F44336;"></span>
            <span>경매</span>
        </div>
    </div>

    <script>
        // 지도 초기화
        var mapContainer = document.getElementById('map');
        var mapOption = {{
            center: new kakao.maps.LatLng(36.5, 127.5),
            level: 13
        }};

        var map = new kakao.maps.Map(mapContainer, mapOption);

        // 실제 데이터
        var DATA_inside = {inside_json};
        var DATA_nearby = {nearby_json};
        var DATA_auction = {auction_json};
        var DATA_public = {public_json};
        var DATA_proj = {proj_json};
        var DATA_rail = {rail_json};
        var DATA_highway = {highway_json};

        // 마커 저장소
        var markers = {{
            railway: [],
            ic: [],
            highway: [],
            development: [],
            inside: [],
            nearby: [],
            auction: [],
            public: [],
            land: []
        }};

        // 레이어 색상 설정
        var layerColors = {{
            railway: '#2196F3',
            ic: '#FF9800',
            highway: '#9C27B0',
            development: '#4CAF50',
            inside: '#E91E63',
            nearby: '#FF5722',
            auction: '#F44336',
            public: '#9C27B0',
            land: 'rgba(76, 175, 80, 0.3)'
        }};

        var curPoly = null;

        // 마커 생성 함수
        function createMarker(category, data, color) {{
            var markerPosition = new kakao.maps.LatLng(data.lat, data.lng);

            // 색상별 원형 마커
            var svg = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">' +
                '<circle cx="12" cy="12" r="10" fill="' + color + '" stroke="white" stroke-width="2"/>' +
                '</svg>'
            );
            var markerImage = new kakao.maps.MarkerImage(svg, new kakao.maps.Size(24, 24), {{offset: new kakao.maps.Point(12, 12)}});

            var marker = new kakao.maps.Marker({{
                position: markerPosition,
                image: markerImage
            }});

            // 인포윈도우 생성
            var infoContent = '<div class="custom-info">';

            if (category === 'railway') {{
                infoContent += '<div class="info-title">🚇 ' + (data.station || data.name) + '</div>' +
                    '<div class="info-content">' +
                    '<div><strong>노선:</strong> ' + (data.line || '') + '</div>' +
                    '<div class="info-badge" style="background:#E3F2FD; color:#2196F3;">철도</div>' +
                    '</div>';
            }} else if (category === 'ic' || category === 'highway') {{
                infoContent += '<div class="info-title">🛣️ ' + data.name + '</div>' +
                    '<div class="info-content">' +
                    '<div><strong>구분:</strong> IC/고속도로</div>' +
                    '<div class="info-badge" style="background:#FFF3E0; color:#FF9800;">교통</div>' +
                    '</div>';
            }} else if (category === 'development') {{
                infoContent += '<div class="info-title">🏗️ ' + data.name + '</div>' +
                    '<div class="info-content">' +
                    '<div><strong>구분:</strong> 개발예정지</div>' +
                    '<div class="info-badge" style="background:#E8F5E9; color:#4CAF50;">개발</div>' +
                    '</div>';
            }} else {{
                // 경공매 (inside, nearby, auction, public)
                infoContent += '<div class="info-title">🏠 ' + data.case_no + '</div>' +
                    '<div class="info-content">' +
                    '<div><strong>위치:</strong> ' + data.address + '</div>' +
                    '<div><strong>용도:</strong> ' + data.usage + '</div>' +
                    '<div><strong>감정가:</strong> ' + formatPrice(data.appraisal) + '</div>' +
                    '<div><strong>최저가:</strong> ' + formatPrice(data.min_price) + ' (' + data.ratio + ')</div>' +
                    '<div><strong>상태:</strong> ' + data.status + '</div>' +
                    '<div><strong>매각일:</strong> ' + data.date + '</div>' +
                    '<div class="info-badge" style="background:#FFEBEE; color:#F44336;">' + getCategoryName(category) + '</div>' +
                    '</div>';
            }}

            infoContent += '</div>';

            var infowindow = new kakao.maps.InfoWindow({{
                content: infoContent,
                removable: true
            }});

            // 마커 클릭 이벤트
            kakao.maps.event.addListener(marker, 'click', function() {{
                infowindow.open(map, marker);
                if (data.lat && data.lng && (category === 'inside' || category === 'nearby' || category === 'auction' || category === 'public')) {{
                    showParcel(data.lat, data.lng, color);
                }}
            }});

            return marker;
        }}

        function formatPrice(p) {{
            if (p >= 100000000) return (p / 100000000).toFixed(1) + '억';
            return Math.round(p / 10000).toLocaleString() + '만원';
        }}

        function getCategoryName(cat) {{
            var names = {{inside: '지구내', nearby: '지구인근', auction: '경매', public: '공매'}};
            return names[cat] || cat;
        }}

        // 필지 폴리곤 표시
        function showParcel(lat, lng, color) {{
            if (curPoly) {{ curPoly.setMap(null); curPoly = null; }}
            map.setCenter(new kakao.maps.LatLng(lat, lng));
            if (map.getLevel() > 3) map.setLevel(3);

            var x = lng * 20037508.34 / 180;
            var y = Math.log(Math.tan((90 + lat) * Math.PI / 360)) / (Math.PI / 180) * 20037508.34 / 180;
            var bbox = (x - 50) + ',' + (y - 50) + ',' + (x + 50) + ',' + (y + 50);

            fetch('/.netlify/functions/vworld?bbox=' + bbox)
                .then(function(r) {{ return r.json(); }})
                .then(function(data) {{
                    if (!data.features || !data.features.length) return;
                    var best = null, minD = Infinity;
                    data.features.forEach(function(f) {{
                        if (!f.geometry || !f.geometry.coordinates) return;
                        var coords = f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates[0][0] : f.geometry.coordinates[0];
                        if (!coords) return;
                        var cx = 0, cy = 0;
                        coords.forEach(function(c) {{ cx += c[0]; cy += c[1]; }});
                        cx /= coords.length; cy /= coords.length;
                        var d = Math.sqrt((cx - x) * (cx - x) + (cy - y) * (cy - y));
                        if (d < minD) {{ minD = d; best = f; }}
                    }});
                    if (!best) return;
                    var coords = best.geometry.type === 'MultiPolygon' ? best.geometry.coordinates[0][0] : best.geometry.coordinates[0];
                    var path = coords.map(function(c) {{
                        var lon = c[0] * 180 / 20037508.34;
                        var la = Math.atan(Math.exp(c[1] * Math.PI / 20037508.34)) * 360 / Math.PI - 90;
                        return new kakao.maps.LatLng(la, lon);
                    }});
                    curPoly = new kakao.maps.Polygon({{
                        path: path,
                        strokeWeight: 3,
                        strokeColor: color,
                        strokeOpacity: 1,
                        fillColor: color,
                        fillOpacity: 0.4,
                        map: map
                    }});
                }})
                .catch(function(e) {{ console.error(e); }});
        }}

        // 데이터 초기화
        function initializeMarkers() {{
            // 철도
            DATA_rail.forEach(function(item) {{
                var marker = createMarker('railway', item, layerColors.railway);
                markers.railway.push(marker);
                marker.setMap(map);
            }});

            // 고속도로/IC
            DATA_highway.forEach(function(item) {{
                var marker = createMarker('ic', item, layerColors.ic);
                markers.ic.push(marker);
                marker.setMap(map);
            }});

            // 개발예정지 (projData에서 좌표가 있는 것만)
            DATA_proj.forEach(function(item) {{
                if (item.path && item.path.length > 0) {{
                    var centerLat = item.path.reduce(function(sum, p) {{ return sum + p[0]; }}, 0) / item.path.length;
                    var centerLng = item.path.reduce(function(sum, p) {{ return sum + p[1]; }}, 0) / item.path.length;
                    var devItem = {{name: item.name, lat: centerLat, lng: centerLng}};
                    var marker = createMarker('development', devItem, layerColors.development);
                    markers.development.push(marker);
                    marker.setMap(map);
                }}
            }});

            // 지구내
            DATA_inside.forEach(function(item) {{
                var marker = createMarker('inside', item, layerColors.inside);
                markers.inside.push(marker);
                marker.setMap(map);
            }});

            // 지구인근
            DATA_nearby.forEach(function(item) {{
                var marker = createMarker('nearby', item, layerColors.nearby);
                markers.nearby.push(marker);
                marker.setMap(map);
            }});

            // 경매 (기본 숨김)
            DATA_auction.forEach(function(item) {{
                var marker = createMarker('auction', item, layerColors.auction);
                markers.auction.push(marker);
                // marker.setMap(map); // 기본 숨김
            }});

            // 공매 (기본 숨김)
            DATA_public.forEach(function(item) {{
                var marker = createMarker('public', item, layerColors.public);
                markers.public.push(marker);
                // marker.setMap(map); // 기본 숨김
            }});

            // 토지보상구역 폴리곤 (기본 숨김)
            DATA_proj.forEach(function(p) {{
                if (!p.path || p.path.length < 3) return;
                var path = p.path.map(function(c) {{ return new kakao.maps.LatLng(c[0], c[1]); }});
                var polygon = new kakao.maps.Polygon({{
                    path: path,
                    strokeWeight: 2,
                    strokeColor: '#4CAF50',
                    strokeOpacity: 0.8,
                    fillColor: '#4CAF50',
                    fillOpacity: 0.2
                }});
                markers.land.push(polygon);
                // polygon.setMap(map); // 기본 숨김
            }});
        }}

        // 레이어 토글
        function toggleLayer(category) {{
            var checkbox = document.getElementById('layer-' + category);
            var isChecked = checkbox.checked;

            markers[category].forEach(function(marker) {{
                marker.setMap(isChecked ? map : null);
            }});

            updateStats();
        }}

        // 통계 업데이트
        function updateStats() {{
            var visible = 0;
            Object.keys(markers).forEach(function(category) {{
                var checkbox = document.getElementById('layer-' + category);
                if (checkbox && checkbox.checked) {{
                    visible += markers[category].length;
                }}
            }});

            document.getElementById('visible-count').textContent = visible.toLocaleString();
        }}

        // 지도 클릭시 폴리곤 제거
        kakao.maps.event.addListener(map, 'click', function() {{
            if (curPoly) {{ curPoly.setMap(null); curPoly = null; }}
        }});

        // 초기화
        initializeMarkers();
        updateStats();

        console.log('✅ 프로토타입 지도 로드 완료!');
        console.log('📊 총 ' + {cnt_total} + '개 경공매 데이터');
    </script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"완료! (경공매 {cnt_total:,}건)")
