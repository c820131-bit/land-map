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
        except:
            data_vars[var_name] = []

# 새 HTML 생성
inside_json = json.dumps(data_vars.get('inside', []), ensure_ascii=False)
nearby_json = json.dumps(data_vars.get('nearby', []), ensure_ascii=False)
auction_json = json.dumps(data_vars.get('auction_data', []), ensure_ascii=False)
public_json = json.dumps(data_vars.get('public_data', []), ensure_ascii=False)
proj_json = json.dumps(data_vars.get('projData', []), ensure_ascii=False)
rail_json = json.dumps(data_vars.get('railData', []), ensure_ascii=False)
highway_json = json.dumps(data_vars.get('highwayData', []), ensure_ascii=False)
dev_json = json.dumps(data_vars.get('devData', []), ensure_ascii=False)

cnt_inside = len(data_vars.get('inside', []))
cnt_nearby = len(data_vars.get('nearby', []))
cnt_auction = len(data_vars.get('auction_data', []))
cnt_public = len(data_vars.get('public_data', []))
cnt_total = cnt_inside + cnt_nearby + cnt_auction + cnt_public

html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>투자지도 PRO - 전국 경공매 {cnt_total:,}건</title>
<style>
:root {{
  --primary: #6366f1;
  --primary-dark: #4f46e5;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --purple: #a855f7;
  --bg: #0f172a;
  --card: #1e293b;
  --border: #334155;
  --text: #f8fafc;
  --text-muted: #94a3b8;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); }}
#map {{ width: 100%; height: 100vh; }}

/* 사이드 패널 */
.panel {{
  position: fixed;
  top: 20px;
  left: 20px;
  width: 340px;
  max-height: calc(100vh - 40px);
  background: var(--card);
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
  z-index: 1000;
  overflow: hidden;
  border: 1px solid var(--border);
}}
.panel-header {{
  padding: 20px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--purple) 100%);
}}
.panel-title {{
  font-size: 24px;
  font-weight: 700;
  color: white;
  margin-bottom: 4px;
}}
.panel-subtitle {{
  font-size: 13px;
  color: rgba(255,255,255,0.8);
}}
.panel-body {{
  padding: 16px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}}
.panel-body::-webkit-scrollbar {{ width: 6px; }}
.panel-body::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

/* 통계 카드 */
.stats {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}}
.stat {{
  background: var(--bg);
  border-radius: 12px;
  padding: 14px;
  text-align: center;
  border: 1px solid var(--border);
}}
.stat-value {{
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary) 0%, var(--purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}
.stat-label {{
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}}

/* 검색 */
.search-box {{
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}}
.search-box input {{
  flex: 1;
  padding: 12px 16px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}}
.search-box input:focus {{
  border-color: var(--primary);
}}
.search-box input::placeholder {{
  color: var(--text-muted);
}}
.search-box button {{
  padding: 12px 20px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}}
.search-box button:hover {{
  background: var(--primary-dark);
}}

/* 섹션 */
.section {{
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 16px 0 8px;
}}

/* 토글 */
.toggle-row {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg);
  border-radius: 10px;
  margin-bottom: 6px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}}
.toggle-row:hover {{
  border-color: var(--border);
}}
.toggle-row.active {{
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
}}
.toggle-icon {{
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}}
.toggle-icon.inside {{ background: rgba(34, 197, 94, 0.2); }}
.toggle-icon.nearby {{ background: rgba(245, 158, 11, 0.2); }}
.toggle-icon.auction {{ background: rgba(59, 130, 246, 0.2); }}
.toggle-icon.public {{ background: rgba(168, 85, 247, 0.2); }}
.toggle-icon.proj {{ background: rgba(6, 182, 212, 0.15); }}
.toggle-icon.rail {{ background: rgba(239, 68, 68, 0.15); }}
.toggle-icon.highway {{ background: rgba(34, 197, 94, 0.15); }}
.toggle-icon.dev {{ background: rgba(251, 191, 36, 0.15); }}
.toggle-info {{
  flex: 1;
}}
.toggle-name {{
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}}
.toggle-count {{
  font-size: 12px;
  color: var(--text-muted);
}}
.toggle-switch {{
  width: 44px;
  height: 24px;
  background: var(--border);
  border-radius: 12px;
  position: relative;
  transition: background 0.2s;
}}
.toggle-switch::after {{
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  top: 3px;
  left: 3px;
  transition: transform 0.2s;
}}
.toggle-row.active .toggle-switch {{
  background: var(--primary);
}}
.toggle-row.active .toggle-switch::after {{
  transform: translateX(20px);
}}

/* 지도 타입 */
.map-types {{
  display: flex;
  gap: 6px;
  margin-top: 16px;
}}
.map-type-btn {{
  flex: 1;
  padding: 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}}
.map-type-btn.active {{
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}}

/* 정보창 */
.info-popup {{
  padding: 16px;
  max-width: 320px;
  font-size: 13px;
  line-height: 1.6;
}}
.info-popup .title {{
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #1a1a1a;
}}
.info-popup .address {{
  color: #666;
  margin-bottom: 12px;
}}
.info-popup .details {{
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 12px;
}}
.info-popup .label {{
  color: #999;
}}
.info-popup .value {{
  font-weight: 500;
}}
.info-popup .price {{
  color: #ef4444;
  font-weight: 700;
}}

/* 로딩 */
.loading {{
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}}
.loading-spinner {{
  width: 48px;
  height: 48px;
  border: 4px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}}
@keyframes spin {{
  to {{ transform: rotate(360deg); }}
}}
.loading-text {{
  margin-top: 16px;
  color: var(--text);
  font-size: 16px;
}}

/* 범례 */
.legend {{
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 16px;
  z-index: 1000;
}}
.legend-title {{
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}}
.legend-item {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
  margin: 4px 0;
}}
.legend-dot {{
  width: 12px;
  height: 12px;
  border-radius: 50%;
}}
</style>
</head>
<body>

<div class="loading" id="loading">
  <div class="loading-spinner"></div>
  <div class="loading-text">투자지도 로딩 중...</div>
</div>

<div id="map"></div>

<div class="panel">
  <div class="panel-header">
    <div class="panel-title">투자지도 PRO</div>
    <div class="panel-subtitle">전국 경공매 {cnt_total:,}건 실시간</div>
  </div>
  <div class="panel-body">
    <div class="stats">
      <div class="stat">
        <div class="stat-value">{cnt_inside + cnt_nearby:,}</div>
        <div class="stat-label">사업지구 연관</div>
      </div>
      <div class="stat">
        <div class="stat-value">{cnt_auction + cnt_public:,}</div>
        <div class="stat-label">일반 경공매</div>
      </div>
    </div>

    <div class="search-box">
      <input type="text" id="searchInput" placeholder="주소 또는 사건번호 검색">
      <button onclick="search()">검색</button>
    </div>

    <div class="section">사업지구 연관 물건</div>
    <div class="toggle-row active" data-layer="inside" onclick="toggleLayer('inside')">
      <div class="toggle-icon inside">📍</div>
      <div class="toggle-info">
        <div class="toggle-name">지구내 물건</div>
        <div class="toggle-count">{cnt_inside:,}건</div>
      </div>
      <div class="toggle-switch"></div>
    </div>
    <div class="toggle-row active" data-layer="nearby" onclick="toggleLayer('nearby')">
      <div class="toggle-icon nearby">📌</div>
      <div class="toggle-info">
        <div class="toggle-name">지구 인근</div>
        <div class="toggle-count">{cnt_nearby:,}건</div>
      </div>
      <div class="toggle-switch"></div>
    </div>

    <div class="section">일반 경공매</div>
    <div class="toggle-row" data-layer="auction" onclick="toggleLayer('auction')">
      <div class="toggle-icon auction">🔵</div>
      <div class="toggle-info">
        <div class="toggle-name">경매</div>
        <div class="toggle-count">{cnt_auction:,}건</div>
      </div>
      <div class="toggle-switch"></div>
    </div>
    <div class="toggle-row" data-layer="public" onclick="toggleLayer('public')">
      <div class="toggle-icon public">🟣</div>
      <div class="toggle-info">
        <div class="toggle-name">공매</div>
        <div class="toggle-count">{cnt_public:,}건</div>
      </div>
      <div class="toggle-switch"></div>
    </div>

    <div class="section">인프라</div>
    <div class="toggle-row" data-layer="proj" onclick="toggleLayer('proj')">
      <div class="toggle-icon proj">🏗️</div>
      <div class="toggle-info">
        <div class="toggle-name">사업지구 경계</div>
        <div class="toggle-count">172개</div>
      </div>
      <div class="toggle-switch"></div>
    </div>
    <div class="toggle-row" data-layer="rail" onclick="toggleLayer('rail')">
      <div class="toggle-icon rail">🚇</div>
      <div class="toggle-info">
        <div class="toggle-name">철도역</div>
        <div class="toggle-count">280개</div>
      </div>
      <div class="toggle-switch"></div>
    </div>
    <div class="toggle-row" data-layer="highway" onclick="toggleLayer('highway')">
      <div class="toggle-icon highway">🛣️</div>
      <div class="toggle-info">
        <div class="toggle-name">고속도로 IC</div>
        <div class="toggle-count">159개</div>
      </div>
      <div class="toggle-switch"></div>
    </div>

    <div class="map-types">
      <button class="map-type-btn active" onclick="setMapType('roadmap')">일반</button>
      <button class="map-type-btn" onclick="setMapType('skyview')">위성</button>
      <button class="map-type-btn" onclick="setMapType('hybrid')">하이브리드</button>
    </div>
  </div>
</div>

<div class="legend">
  <div class="legend-title">마커 범례</div>
  <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div>지구내 물건</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>지구 인근</div>
  <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div>일반 경매</div>
  <div class="legend-item"><div class="legend-dot" style="background:#a855f7"></div>공매</div>
</div>

<script>
// 데이터
var DATA = {{
  inside: {inside_json},
  nearby: {nearby_json},
  auction: {auction_json},
  public: {public_json}
}};
var projData = {proj_json};
var railData = {rail_json};
var highwayData = {highway_json};
var devData = {dev_json};

// 전역 변수
var map, clusterer;
var layers = {{ proj: [], rail: [], highway: [], dev: [] }};
var layerMarkers = {{ inside: [], nearby: [], auction: [], public: [] }};
var layerVisible = {{ inside: true, nearby: true, auction: false, public: false, proj: false, rail: false, highway: false }};
var currentPolygon = null;

// 색상
var COLORS = {{
  inside: '#22c55e',
  nearby: '#f59e0b',
  auction: '#3b82f6',
  public: '#a855f7'
}};

// 지도 초기화
function initMap() {{
  var container = document.getElementById('map');
  var options = {{
    center: new kakao.maps.LatLng(36.5, 127.5),
    level: 13
  }};
  map = new kakao.maps.Map(container, options);

  // 클러스터러 생성
  clusterer = new kakao.maps.MarkerClusterer({{
    map: map,
    averageCenter: true,
    minLevel: 6,
    disableClickZoom: true,
    styles: [
      {{ width: '50px', height: '50px', background: 'rgba(99, 102, 241, 0.9)', borderRadius: '50%', color: '#fff', textAlign: 'center', fontWeight: 'bold', lineHeight: '50px', fontSize: '14px' }},
      {{ width: '60px', height: '60px', background: 'rgba(99, 102, 241, 0.9)', borderRadius: '50%', color: '#fff', textAlign: 'center', fontWeight: 'bold', lineHeight: '60px', fontSize: '16px' }},
      {{ width: '70px', height: '70px', background: 'rgba(99, 102, 241, 0.9)', borderRadius: '50%', color: '#fff', textAlign: 'center', fontWeight: 'bold', lineHeight: '70px', fontSize: '18px' }}
    ]
  }});

  // 마커 생성
  createMarkers();

  // 초기 레이어 표시
  updateClusterer();

  // 사업지구 경계 생성
  createProjectBoundaries();
  createRailMarkers();
  createHighwayMarkers();

  // 지도 클릭 시 폴리곤 숨기기
  kakao.maps.event.addListener(map, 'click', function() {{
    if (currentPolygon) {{
      currentPolygon.setMap(null);
      currentPolygon = null;
    }}
  }});

  // 로딩 완료
  document.getElementById('loading').style.display = 'none';
}}

// 마커 생성
function createMarkers() {{
  ['inside', 'nearby', 'auction', 'public'].forEach(function(type) {{
    var color = COLORS[type];
    DATA[type].forEach(function(item) {{
      var marker = createMarker(item, color, type);
      layerMarkers[type].push(marker);
    }});
  }});
}}

function createMarker(item, color, type) {{
  var svg = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="10" fill="' + color + '" stroke="#fff" stroke-width="2"/></svg>');
  var image = new kakao.maps.MarkerImage(svg, new kakao.maps.Size(24, 24), {{ offset: new kakao.maps.Point(12, 12) }});
  var marker = new kakao.maps.Marker({{
    position: new kakao.maps.LatLng(item.lat, item.lng),
    image: image
  }});

  // 정보창
  var content = '<div class="info-popup">' +
    '<div class="title">' + item.case_no + '</div>' +
    '<div class="address">' + item.address + '</div>' +
    '<div class="details">' +
      '<span class="label">용도</span><span class="value">' + item.usage + '</span>' +
      '<span class="label">감정가</span><span class="value price">' + formatPrice(item.appraisal) + '</span>' +
      '<span class="label">최저가</span><span class="value price">' + formatPrice(item.min_price) + ' (' + item.ratio + ')</span>' +
      '<span class="label">상태</span><span class="value">' + item.status + '</span>' +
      '<span class="label">매각일</span><span class="value">' + item.date + '</span>' +
    '</div></div>';

  var infowindow = new kakao.maps.InfoWindow({{ content: content, removable: true }});

  kakao.maps.event.addListener(marker, 'click', function() {{
    infowindow.open(map, marker);
    showParcel(item.lat, item.lng, type);
  }});

  marker._data = item;
  marker._type = type;
  return marker;
}}

function formatPrice(price) {{
  if (price >= 100000000) {{
    return (price / 100000000).toFixed(1) + '억';
  }} else {{
    return (price / 10000).toLocaleString() + '만원';
  }}
}}

// 클러스터러 업데이트
function updateClusterer() {{
  var markers = [];
  ['inside', 'nearby', 'auction', 'public'].forEach(function(type) {{
    if (layerVisible[type]) {{
      markers = markers.concat(layerMarkers[type]);
    }}
  }});
  clusterer.clear();
  clusterer.addMarkers(markers);
}}

// 레이어 토글
function toggleLayer(layer) {{
  var row = document.querySelector('[data-layer="' + layer + '"]');
  layerVisible[layer] = !layerVisible[layer];
  row.classList.toggle('active', layerVisible[layer]);

  if (layer === 'inside' || layer === 'nearby' || layer === 'auction' || layer === 'public') {{
    updateClusterer();
  }} else if (layer === 'proj') {{
    layers.proj.forEach(function(p) {{ p.setMap(layerVisible.proj ? map : null); }});
  }} else if (layer === 'rail') {{
    layers.rail.forEach(function(m) {{ m.setMap(layerVisible.rail ? map : null); }});
  }} else if (layer === 'highway') {{
    layers.highway.forEach(function(m) {{ m.setMap(layerVisible.highway ? map : null); }});
  }}
}}

// 사업지구 경계
function createProjectBoundaries() {{
  projData.forEach(function(proj) {{
    if (!proj.path || proj.path.length < 3) return;
    var path = proj.path.map(function(p) {{ return new kakao.maps.LatLng(p[0], p[1]); }});
    var polygon = new kakao.maps.Polygon({{
      path: path,
      strokeWeight: 2,
      strokeColor: '#06b6d4',
      strokeOpacity: 0.8,
      fillColor: '#06b6d4',
      fillOpacity: 0.1
    }});
    var infowindow = new kakao.maps.InfoWindow({{
      content: '<div style="padding:8px;font-size:12px;font-weight:bold">' + proj.name + '</div>'
    }});
    kakao.maps.event.addListener(polygon, 'mouseover', function() {{
      infowindow.setPosition(path[0]);
      infowindow.open(map);
    }});
    kakao.maps.event.addListener(polygon, 'mouseout', function() {{
      infowindow.close();
    }});
    layers.proj.push(polygon);
  }});
}}

// 철도역
function createRailMarkers() {{
  railData.forEach(function(r) {{
    var isSubway = r.line && (r.line.includes('호선') || r.line.includes('GTX') || r.line.includes('신분당'));
    var emoji = isSubway ? '🚇' : '🚄';
    var svg = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><text x="12" y="18" font-size="18" text-anchor="middle">' + emoji + '</text></svg>');
    var marker = new kakao.maps.Marker({{
      position: new kakao.maps.LatLng(r.lat, r.lng),
      image: new kakao.maps.MarkerImage(svg, new kakao.maps.Size(24, 24))
    }});
    var infowindow = new kakao.maps.InfoWindow({{
      content: '<div style="padding:8px;font-size:12px"><b>' + (r.station || r.name) + '</b><br>' + (r.line || '') + '</div>'
    }});
    kakao.maps.event.addListener(marker, 'mouseover', function() {{ infowindow.open(map, marker); }});
    kakao.maps.event.addListener(marker, 'mouseout', function() {{ infowindow.close(); }});
    layers.rail.push(marker);
  }});
}}

// 고속도로 IC
function createHighwayMarkers() {{
  highwayData.forEach(function(h) {{
    var svg = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="14"><rect width="20" height="14" rx="3" fill="#16a34a"/><text x="10" y="10" font-size="8" fill="#fff" text-anchor="middle" font-weight="bold">IC</text></svg>');
    var marker = new kakao.maps.Marker({{
      position: new kakao.maps.LatLng(h.lat, h.lng),
      image: new kakao.maps.MarkerImage(svg, new kakao.maps.Size(20, 14))
    }});
    var infowindow = new kakao.maps.InfoWindow({{
      content: '<div style="padding:8px;font-size:12px"><b>' + h.name + '</b></div>'
    }});
    kakao.maps.event.addListener(marker, 'mouseover', function() {{ infowindow.open(map, marker); }});
    kakao.maps.event.addListener(marker, 'mouseout', function() {{ infowindow.close(); }});
    layers.highway.push(marker);
  }});
}}

// 필지 폴리곤 표시
function showParcel(lat, lng, type) {{
  if (currentPolygon) {{
    currentPolygon.setMap(null);
    currentPolygon = null;
  }}
  map.setCenter(new kakao.maps.LatLng(lat, lng));
  if (map.getLevel() > 3) map.setLevel(3);

  var x = lng * 20037508.34 / 180;
  var y = Math.log(Math.tan((90 + lat) * Math.PI / 360)) / (Math.PI / 180) * 20037508.34 / 180;
  var bbox = (x - 50) + ',' + (y - 50) + ',' + (x + 50) + ',' + (y + 50);

  fetch('/.netlify/functions/vworld?bbox=' + bbox)
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (!data.features || !data.features.length) return;

      var best = null, minDist = Infinity;
      data.features.forEach(function(f) {{
        if (!f.geometry || !f.geometry.coordinates) return;
        var coords = f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates[0][0] : f.geometry.coordinates[0];
        if (!coords || !coords.length) return;
        var cx = 0, cy = 0;
        coords.forEach(function(c) {{ cx += c[0]; cy += c[1]; }});
        cx /= coords.length; cy /= coords.length;
        var dist = Math.sqrt((cx - x) * (cx - x) + (cy - y) * (cy - y));
        if (dist < minDist) {{ minDist = dist; best = f; }}
      }});

      if (!best) return;

      var coords = best.geometry.type === 'MultiPolygon' ? best.geometry.coordinates[0][0] : best.geometry.coordinates[0];
      var path = coords.map(function(c) {{
        var lon = c[0] * 180 / 20037508.34;
        var la = Math.atan(Math.exp(c[1] * Math.PI / 20037508.34)) * 360 / Math.PI - 90;
        return new kakao.maps.LatLng(la, lon);
      }});

      currentPolygon = new kakao.maps.Polygon({{
        path: path,
        strokeWeight: 3,
        strokeColor: COLORS[type] || '#333',
        strokeOpacity: 1,
        fillColor: COLORS[type] || '#333',
        fillOpacity: 0.4,
        map: map
      }});
    }})
    .catch(function(e) {{ console.error('Parcel error:', e); }});
}}

// 검색
function search() {{
  var q = document.getElementById('searchInput').value.toLowerCase().trim();
  if (!q) return;

  var found = null;
  ['inside', 'nearby', 'auction', 'public'].forEach(function(type) {{
    if (found) return;
    DATA[type].forEach(function(item) {{
      if (found) return;
      if (item.address.toLowerCase().includes(q) || item.case_no.toLowerCase().includes(q)) {{
        found = {{ item: item, type: type }};
      }}
    }});
  }});

  if (found) {{
    // 해당 레이어 활성화
    if (!layerVisible[found.type]) {{
      toggleLayer(found.type);
    }}
    map.setCenter(new kakao.maps.LatLng(found.item.lat, found.item.lng));
    map.setLevel(3);
    showParcel(found.item.lat, found.item.lng, found.type);
  }} else {{
    alert('검색 결과가 없습니다.');
  }}
}}

// 엔터키 검색
document.getElementById('searchInput').addEventListener('keypress', function(e) {{
  if (e.key === 'Enter') search();
}});

// 지도 타입 변경
function setMapType(type) {{
  document.querySelectorAll('.map-type-btn').forEach(function(btn) {{
    btn.classList.remove('active');
  }});
  event.target.classList.add('active');

  if (type === 'roadmap') {{
    map.setMapTypeId(kakao.maps.MapTypeId.ROADMAP);
  }} else if (type === 'skyview') {{
    map.setMapTypeId(kakao.maps.MapTypeId.SKYVIEW);
  }} else if (type === 'hybrid') {{
    map.setMapTypeId(kakao.maps.MapTypeId.HYBRID);
  }}
}}
</script>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=7e60f6a42602355b925c66ea6db3bd87&libraries=clusterer&autoload=false"></script>
<script>
kakao.maps.load(initMap);
</script>
</body>
</html>'''

# 새 HTML 저장
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"새 index.html 생성 완료!")
print(f"총 {cnt_total:,}건의 경공매 데이터 포함")
