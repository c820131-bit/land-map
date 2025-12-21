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
    <title>Investment Map Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; overflow: hidden; background: #0a0a0a; }}
        #map {{ width: 100vw; height: 100vh; }}

        /* 글래스모피즘 컨트롤 패널 */
        .control-panel {{
            position: absolute; top: 24px; left: 24px;
            background: rgba(18, 18, 22, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 24px;
            min-width: 300px;
            max-height: calc(100vh - 48px);
            overflow-y: auto;
            z-index: 100;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
        }}
        .control-panel::-webkit-scrollbar {{ width: 4px; }}
        .control-panel::-webkit-scrollbar-track {{ background: transparent; }}
        .control-panel::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 2px; }}

        .panel-header {{
            font-size: 15px;
            font-weight: 600;
            letter-spacing: -0.3px;
            margin-bottom: 20px;
            color: rgba(255,255,255,0.95);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .panel-header::before {{
            content: '';
            width: 4px;
            height: 18px;
            background: linear-gradient(180deg, #6366f1, #8b5cf6);
            border-radius: 2px;
        }}

        .layer-group {{ margin-bottom: 20px; }}
        .layer-title {{
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 12px;
            color: rgba(255,255,255,0.4);
        }}

        .layer-item {{
            display: flex;
            align-items: center;
            padding: 12px 14px;
            margin-bottom: 6px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .layer-item:hover {{
            background: rgba(255,255,255,0.06);
            border-color: rgba(255,255,255,0.08);
        }}

        /* 커스텀 토글 스위치 */
        .toggle-wrap {{ position: relative; margin-right: 12px; }}
        .layer-item input[type="checkbox"] {{
            position: absolute;
            opacity: 0;
            width: 0;
            height: 0;
        }}
        .toggle {{
            width: 36px;
            height: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            position: relative;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .toggle::after {{
            content: '';
            position: absolute;
            width: 16px;
            height: 16px;
            background: rgba(255,255,255,0.5);
            border-radius: 50%;
            top: 2px;
            left: 2px;
            transition: all 0.3s ease;
        }}
        .layer-item input:checked + .toggle {{
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
        }}
        .layer-item input:checked + .toggle::after {{
            left: 18px;
            background: #fff;
        }}

        .layer-color {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 0 8px currentColor;
        }}
        .layer-name {{
            flex: 1;
            font-size: 13px;
            font-weight: 400;
            color: rgba(255,255,255,0.85);
        }}
        .layer-count {{
            font-size: 11px;
            font-weight: 500;
            color: rgba(255,255,255,0.4);
            background: rgba(255,255,255,0.05);
            padding: 4px 10px;
            border-radius: 6px;
        }}

        /* 통계 패널 */
        .stats-panel {{
            position: absolute;
            top: 24px;
            right: 24px;
            background: rgba(18, 18, 22, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 24px;
            min-width: 200px;
            z-index: 100;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }}
        .stats-title {{
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 16px;
            color: rgba(255,255,255,0.4);
        }}
        .stat-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .stat-item:last-child {{ border-bottom: none; }}
        .stat-label {{ font-size: 13px; color: rgba(255,255,255,0.6); }}
        .stat-value {{
            font-size: 16px;
            font-weight: 600;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        /* 범례 */
        .legend {{
            position: absolute;
            bottom: 24px;
            left: 24px;
            background: rgba(18, 18, 22, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            padding: 16px 20px;
            z-index: 100;
            display: flex;
            gap: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 11px;
            color: rgba(255,255,255,0.6);
        }}
        .legend-item span:first-child {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
            box-shadow: 0 0 6px currentColor;
        }}

        /* 로고 */
        .logo {{
            position: absolute;
            bottom: 24px;
            right: 24px;
            background: rgba(18, 18, 22, 0.85);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 10px 16px;
            z-index: 100;
            font-size: 12px;
            font-weight: 600;
            color: rgba(255,255,255,0.5);
            letter-spacing: 1px;
        }}

        /* 지도 타입 선택 */
        .map-type-selector {{
            position: absolute;
            top: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(18, 18, 22, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 6px;
            z-index: 100;
            display: flex;
            gap: 4px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }}
        .map-type-btn {{
            padding: 10px 20px;
            border: none;
            background: transparent;
            color: rgba(255,255,255,0.5);
            font-family: 'Pretendard', sans-serif;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s ease;
        }}
        .map-type-btn:hover {{
            color: rgba(255,255,255,0.8);
            background: rgba(255,255,255,0.05);
        }}
        .map-type-btn.active {{
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: #fff;
        }}

        /* 줌 컨트롤 */
        .zoom-control {{
            position: absolute;
            bottom: 100px;
            right: 24px;
            background: rgba(18, 18, 22, 0.85);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            overflow: hidden;
            z-index: 100;
            display: flex;
            flex-direction: column;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }}
        .zoom-btn {{
            width: 44px;
            height: 44px;
            border: none;
            background: transparent;
            color: rgba(255,255,255,0.7);
            font-size: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .zoom-btn:hover {{
            background: rgba(255,255,255,0.1);
            color: #fff;
        }}
        .zoom-btn:first-child {{
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
    </style>
</head>
<body>
    <div id="map"></div>

    <!-- 지도 타입 선택 -->
    <div class="map-type-selector">
        <button class="map-type-btn active" onclick="setMapType('roadmap')">일반</button>
        <button class="map-type-btn" onclick="setMapType('skyview')">스카이뷰</button>
        <button class="map-type-btn" onclick="setMapType('hybrid')">하이브리드</button>
    </div>

    <!-- 줌 컨트롤 -->
    <div class="zoom-control">
        <button class="zoom-btn" onclick="zoomIn()">+</button>
        <button class="zoom-btn" onclick="zoomOut()">−</button>
    </div>

    <div class="control-panel">
        <div class="panel-header">레이어 컨트롤</div>
        <div class="layer-group">
            <div class="layer-title">Infrastructure</div>
            <label class="layer-item">
                <input type="checkbox" id="layer-railway" onchange="toggleLayer('railway')">
                <div class="toggle"></div>
                <div class="layer-color" style="background: #3b82f6; color: #3b82f6;"></div>
                <span class="layer-name">철도예정지</span>
                <span class="layer-count">{cnt_rail}</span>
            </label>
            <label class="layer-item">
                <input type="checkbox" id="layer-highway" onchange="toggleLayer('highway')">
                <div class="toggle"></div>
                <div class="layer-color" style="background: #f59e0b; color: #f59e0b;"></div>
                <span class="layer-name">고속도로 IC</span>
                <span class="layer-count">{cnt_highway}</span>
            </label>
        </div>
        <div class="layer-group">
            <div class="layer-title">Development & Auction</div>
            <label class="layer-item">
                <input type="checkbox" id="layer-land" onchange="toggleLayer('land')">
                <div class="toggle"></div>
                <div class="layer-color" style="background: #f97316; color: #f97316;"></div>
                <span class="layer-name">사업지구 경계</span>
                <span class="layer-count">{cnt_proj}</span>
            </label>
            <label class="layer-item">
                <input type="checkbox" id="layer-development" onchange="toggleLayer('development')">
                <div class="toggle"></div>
                <div class="layer-color" style="background: #22c55e; color: #22c55e;"></div>
                <span class="layer-name">개발예정지</span>
                <span class="layer-count">{cnt_proj}</span>
            </label>
            <label class="layer-item">
                <input type="checkbox" id="layer-inside" checked onchange="toggleLayer('inside')">
                <div class="toggle"></div>
                <div class="layer-color" style="background: #ec4899; color: #ec4899;"></div>
                <span class="layer-name">지구내 경공매</span>
                <span class="layer-count">{cnt_inside}</span>
            </label>
            <label class="layer-item">
                <input type="checkbox" id="layer-nearby" checked onchange="toggleLayer('nearby')">
                <div class="toggle"></div>
                <div class="layer-color" style="background: #f97316; color: #f97316;"></div>
                <span class="layer-name">지구인근 경공매</span>
                <span class="layer-count">{cnt_nearby}</span>
            </label>
            <label class="layer-item">
                <input type="checkbox" id="layer-auction" onchange="toggleLayer('auction')">
                <div class="toggle"></div>
                <div class="layer-color" style="background: #ef4444; color: #ef4444;"></div>
                <span class="layer-name">경매</span>
                <span class="layer-count">{cnt_auction}</span>
            </label>
            <label class="layer-item">
                <input type="checkbox" id="layer-public" onchange="toggleLayer('public')">
                <div class="toggle"></div>
                <div class="layer-color" style="background: #a855f7; color: #a855f7;"></div>
                <span class="layer-name">공매</span>
                <span class="layer-count">{cnt_public}</span>
            </label>
        </div>
    </div>

    <div class="stats-panel">
        <div class="stats-title">Statistics</div>
        <div class="stat-item"><span class="stat-label">전체 물건</span><span class="stat-value">{cnt_total:,}</span></div>
        <div class="stat-item"><span class="stat-label">지구내</span><span class="stat-value">{cnt_inside:,}</span></div>
        <div class="stat-item"><span class="stat-label">지구인근</span><span class="stat-value">{cnt_nearby:,}</span></div>
        <div class="stat-item"><span class="stat-label">사업지구</span><span class="stat-value">{cnt_proj}</span></div>
    </div>

    <div class="legend">
        <div class="legend-item"><span style="background: #f97316; color: #f97316;"></span><span>사업지구</span></div>
        <div class="legend-item"><span style="background: #3b82f6; color: #3b82f6;"></span><span>철도</span></div>
        <div class="legend-item"><span style="background: #f59e0b; color: #f59e0b;"></span><span>IC</span></div>
        <div class="legend-item"><span style="background: #ec4899; color: #ec4899;"></span><span>지구내</span></div>
        <div class="legend-item"><span style="background: #ef4444; color: #ef4444;"></span><span>경매</span></div>
        <div class="legend-item"><span style="background: #a855f7; color: #a855f7;"></span><span>공매</span></div>
    </div>

    <div class="logo">INVESTMENT MAP</div>

<script>
var DATA_inside = {inside_json};
var DATA_nearby = {nearby_json};
var DATA_auction = {auction_json};
var DATA_public = {public_json};
var DATA_proj = {proj_json};
var DATA_rail = {rail_json};
var DATA_highway = {highway_json};

var COLORS = {{
    railway: '#3b82f6',
    highway: '#f59e0b',
    development: '#22c55e',
    inside: '#ec4899',
    nearby: '#f97316',
    auction: '#ef4444',
    public: '#a855f7'
}};

var map, curPoly = null;
var markers = {{
    railway: [],
    highway: [],
    development: [],
    inside: [],
    nearby: [],
    auction: [],
    public: [],
    land: []
}};

function init() {{
    var container = document.getElementById('map');
    map = new kakao.maps.Map(container, {{
        center: new kakao.maps.LatLng(36.5, 127.5),
        level: 13
    }});

    // 철도
    DATA_rail.forEach(function(d) {{
        var m = createMarker(d.lat, d.lng, COLORS.railway, 'rail');
        var info = '<div style="padding:14px 18px;background:#1a1a1f;color:#fff;border-radius:10px;border:1px solid rgba(255,255,255,0.1);font-family:Pretendard,sans-serif"><div style="font-weight:600;font-size:14px;margin-bottom:4px">' + (d.station || d.name) + '</div><div style="color:rgba(255,255,255,0.5);font-size:12px">' + (d.line || '철도예정지') + '</div></div>';
        addClickEvent(m, info);
        markers.railway.push(m);
    }});

    // 고속도로IC
    DATA_highway.forEach(function(d) {{
        var m = createMarker(d.lat, d.lng, COLORS.highway, 'highway');
        var info = '<div style="padding:14px 18px;background:#1a1a1f;color:#fff;border-radius:10px;border:1px solid rgba(255,255,255,0.1);font-family:Pretendard,sans-serif"><div style="font-weight:600;font-size:14px">' + d.name + '</div><div style="color:rgba(255,255,255,0.5);font-size:12px;margin-top:4px">고속도로 IC</div></div>';
        addClickEvent(m, info);
        markers.highway.push(m);
    }});

    // 개발예정지
    DATA_proj.forEach(function(d) {{
        if (d.path && d.path.length > 0) {{
            var lat = d.path.reduce(function(s, p) {{ return s + p[0]; }}, 0) / d.path.length;
            var lng = d.path.reduce(function(s, p) {{ return s + p[1]; }}, 0) / d.path.length;
            var m = createMarker(lat, lng, COLORS.development, 'dev');
            var info = '<div style="padding:14px 18px;background:#1a1a1f;color:#fff;border-radius:10px;border:1px solid rgba(255,255,255,0.1);font-family:Pretendard,sans-serif;max-width:280px"><div style="font-weight:600;font-size:13px">' + d.name + '</div><div style="color:rgba(255,255,255,0.5);font-size:11px;margin-top:6px">개발예정지</div></div>';
            addClickEvent(m, info);
            markers.development.push(m);
        }}
    }});

    // 지구내
    DATA_inside.forEach(function(d) {{
        var m = createMarker(d.lat, d.lng, COLORS.inside, 'auction');
        var info = createAuctionInfo(d, '지구내');
        addClickEvent(m, info, d);
        markers.inside.push(m);
        m.setMap(map); // 기본 표시
    }});

    // 지구인근
    DATA_nearby.forEach(function(d) {{
        var m = createMarker(d.lat, d.lng, COLORS.nearby, 'auction');
        var info = createAuctionInfo(d, '지구인근');
        addClickEvent(m, info, d);
        markers.nearby.push(m);
        m.setMap(map); // 기본 표시
    }});

    // 경매
    DATA_auction.forEach(function(d) {{
        var m = createMarker(d.lat, d.lng, COLORS.auction, 'auction');
        var info = createAuctionInfo(d, '경매');
        addClickEvent(m, info, d);
        markers.auction.push(m);
    }});

    // 공매
    DATA_public.forEach(function(d) {{
        var m = createMarker(d.lat, d.lng, COLORS.public, 'public');
        var info = createAuctionInfo(d, '공매');
        addClickEvent(m, info, d);
        markers.public.push(m);
    }});

    // 토지보상구역 폴리곤 (경계선 강조)
    DATA_proj.forEach(function(d) {{
        if (!d.path || d.path.length < 3) return;
        var path = d.path.map(function(c) {{ return new kakao.maps.LatLng(c[0], c[1]); }});

        // 폴리곤 (채우기)
        var poly = new kakao.maps.Polygon({{
            path: path,
            strokeWeight: 2,
            strokeColor: '#f97316',
            strokeOpacity: 0.9,
            strokeStyle: 'solid',
            fillColor: '#f97316',
            fillOpacity: 0.12
        }});

        // 클릭 시 사업명 표시
        var name = d.name || '사업지구';
        var infowindow = new kakao.maps.InfoWindow({{
            content: '<div style="padding:14px 18px;font-size:13px;font-weight:500;max-width:280px;background:#1a1a1f;color:#fff;border-radius:8px;border:1px solid rgba(255,255,255,0.1)">' + name + '</div>',
            removable: true
        }});
        kakao.maps.event.addListener(poly, 'click', function(mouseEvent) {{
            infowindow.open(map, mouseEvent.latLng);
        }});

        markers.land.push(poly);
    }});

    kakao.maps.event.addListener(map, 'click', function() {{
        if (curPoly) {{ curPoly.setMap(null); curPoly = null; }}
    }});

    console.log('지도 초기화 완료!');
    console.log('지구내:', markers.inside.length);
    console.log('지구인근:', markers.nearby.length);
}}

function createMarker(lat, lng, color, type) {{
    var size = 10;
    var svg;

    if (type === 'rail') {{
        // 철도 - 기차 이모지
        svg = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
            '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><text x="10" y="15" font-size="14" text-anchor="middle">🚂</text></svg>'
        );
        size = 20;
    }} else if (type === 'highway') {{
        // 고속도로 IC
        svg = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
            '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><text x="10" y="15" font-size="14" text-anchor="middle">🛣️</text></svg>'
        );
        size = 20;
    }} else if (type === 'dev') {{
        // 개발예정지
        svg = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
            '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><text x="10" y="15" font-size="14" text-anchor="middle">🏗️</text></svg>'
        );
        size = 20;
    }} else if (type === 'auction') {{
        // 경매 - "경" 텍스트
        svg = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">' +
            '<circle cx="8" cy="8" r="7" fill="' + color + '" stroke="white" stroke-width="1"/>' +
            '<text x="8" y="12" font-size="9" font-weight="bold" fill="white" text-anchor="middle" font-family="sans-serif">경</text></svg>'
        );
        size = 16;
    }} else if (type === 'public') {{
        // 공매 - "공" 텍스트
        svg = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">' +
            '<circle cx="8" cy="8" r="7" fill="' + color + '" stroke="white" stroke-width="1"/>' +
            '<text x="8" y="12" font-size="9" font-weight="bold" fill="white" text-anchor="middle" font-family="sans-serif">공</text></svg>'
        );
        size = 16;
    }} else {{
        // 기본 원형 (더 작게)
        svg = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">' +
            '<circle cx="5" cy="5" r="4" fill="' + color + '" stroke="white" stroke-width="1"/></svg>'
        );
        size = 10;
    }}

    var img = new kakao.maps.MarkerImage(svg, new kakao.maps.Size(size, size), {{offset: new kakao.maps.Point(size/2, size/2)}});
    return new kakao.maps.Marker({{
        position: new kakao.maps.LatLng(lat, lng),
        image: img
    }});
}}

function createAuctionInfo(d, type) {{
    var typeColor = type === '공매' ? '#a855f7' : '#ef4444';
    return '<div style="padding:16px 20px;max-width:300px;font-size:12px;line-height:1.7;background:#1a1a1f;color:#e5e5e5;border-radius:12px;border:1px solid rgba(255,255,255,0.1);font-family:Pretendard,sans-serif">' +
        '<div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:8px">' + d.case_no + '</div>' +
        '<div style="color:rgba(255,255,255,0.5);font-size:11px;margin-bottom:12px">' + d.address + '</div>' +
        '<div style="display:grid;gap:6px">' +
        '<div style="display:flex;justify-content:space-between"><span style="color:rgba(255,255,255,0.5)">용도</span><span>' + d.usage + '</span></div>' +
        '<div style="display:flex;justify-content:space-between"><span style="color:rgba(255,255,255,0.5)">감정가</span><span style="color:#6366f1;font-weight:600">' + formatPrice(d.appraisal) + '</span></div>' +
        '<div style="display:flex;justify-content:space-between"><span style="color:rgba(255,255,255,0.5)">최저가</span><span style="color:#a855f7;font-weight:600">' + formatPrice(d.min_price) + ' <span style="color:rgba(255,255,255,0.4);font-weight:400">(' + d.ratio + ')</span></span></div>' +
        '</div>' +
        '<div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;align-items:center">' +
        '<span style="color:rgba(255,255,255,0.4);font-size:11px">' + d.status + ' | ' + d.date + '</span>' +
        '<span style="background:' + typeColor + ';color:#fff;padding:3px 10px;border-radius:6px;font-size:10px;font-weight:500">' + type + '</span></div></div>';
}}

function formatPrice(p) {{
    if (p >= 100000000) return (p / 100000000).toFixed(1) + '억';
    return Math.round(p / 10000).toLocaleString() + '만원';
}}

function addClickEvent(marker, infoContent, data) {{
    var infowindow = new kakao.maps.InfoWindow({{ content: infoContent, removable: true }});
    kakao.maps.event.addListener(marker, 'click', function() {{
        infowindow.open(map, marker);
        if (data && data.lat && data.lng) {{
            showParcel(data.lat, data.lng);
        }}
    }});
}}

function showParcel(lat, lng) {{
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
                path: path, strokeWeight: 2, strokeColor: '#6366f1', strokeOpacity: 1,
                fillColor: '#6366f1', fillOpacity: 0.3, map: map
            }});
        }}).catch(function(e) {{ console.error(e); }});
}}

function toggleLayer(category) {{
    var chk = document.getElementById('layer-' + category);
    var show = chk.checked;
    markers[category].forEach(function(m) {{
        m.setMap(show ? map : null);
    }});
}}

// 지도 타입 변경
function setMapType(type) {{
    var mapTypes = {{
        'roadmap': kakao.maps.MapTypeId.ROADMAP,
        'skyview': kakao.maps.MapTypeId.SKYVIEW,
        'hybrid': kakao.maps.MapTypeId.HYBRID
    }};

    // 기존 타입 제거
    map.removeOverlayMapTypeId(kakao.maps.MapTypeId.ROADMAP);
    map.removeOverlayMapTypeId(kakao.maps.MapTypeId.SKYVIEW);
    map.removeOverlayMapTypeId(kakao.maps.MapTypeId.HYBRID);

    // 새 타입 설정
    map.setMapTypeId(mapTypes[type]);

    // 버튼 활성화 상태 변경
    document.querySelectorAll('.map-type-btn').forEach(function(btn) {{
        btn.classList.remove('active');
    }});
    event.target.classList.add('active');
}}

// 줌 컨트롤
function zoomIn() {{
    map.setLevel(map.getLevel() - 1);
}}

function zoomOut() {{
    map.setLevel(map.getLevel() + 1);
}}
</script>
<script>
(function() {{
    var s = document.createElement('script');
    s.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey=7e60f6a42602355b925c66ea6db3bd87&autoload=false';
    s.onload = function() {{
        kakao.maps.load(init);
    }};
    document.head.appendChild(s);
}})();
</script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"완료! ({cnt_total:,}건)")
