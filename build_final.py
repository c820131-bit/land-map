import re
import json
import subprocess

# 데이터 추출
result = subprocess.run(['git', 'show', '867e827:index.html'], capture_output=True, text=True, encoding='utf-8')
content = result.stdout

data_vars = {}
for var_name in ['inside', 'nearby', 'auction_data', 'public_data', 'projData', 'railData', 'highwayData']:
    pattern = rf'var {var_name}=(\[.*?\]);'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        try:
            data_vars[var_name] = json.loads(match.group(1))
            print(f"{var_name}: {len(data_vars[var_name])}건")
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
cnt_total = cnt_inside + cnt_nearby + cnt_auction + cnt_public

html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>투자지도 PRO - {cnt_total:,}건</title>
<style>
:root {{--primary:#6366f1;--success:#22c55e;--warning:#f59e0b;--purple:#a855f7;--bg:#0f172a;--card:#1e293b;--border:#334155;--text:#f8fafc;--muted:#94a3b8}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg)}}
#map{{width:100%;height:100vh}}
.panel{{position:fixed;top:16px;left:16px;width:320px;max-height:calc(100vh - 32px);background:var(--card);border-radius:16px;box-shadow:0 20px 40px rgba(0,0,0,0.4);z-index:1000;overflow:hidden;border:1px solid var(--border)}}
.panel-header{{padding:20px;background:linear-gradient(135deg,var(--primary) 0%,var(--purple) 100%);color:white}}
.panel-title{{font-size:22px;font-weight:700}}
.panel-sub{{font-size:12px;opacity:0.9;margin-top:4px}}
.panel-body{{padding:16px;max-height:calc(100vh - 180px);overflow-y:auto}}
.panel-body::-webkit-scrollbar{{width:5px}}
.panel-body::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}
.stats{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px}}
.stat{{background:var(--bg);border-radius:10px;padding:12px;text-align:center;border:1px solid var(--border)}}
.stat-val{{font-size:20px;font-weight:700;color:var(--primary)}}
.stat-lbl{{font-size:10px;color:var(--muted);margin-top:2px}}
.search{{display:flex;gap:8px;margin-bottom:16px}}
.search input{{flex:1;padding:10px 14px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:13px;outline:none}}
.search input:focus{{border-color:var(--primary)}}
.search button{{padding:10px 16px;background:var(--primary);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer}}
.section{{font-size:10px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin:14px 0 8px}}
.toggle{{display:flex;align-items:center;gap:10px;padding:10px;background:var(--bg);border-radius:8px;margin-bottom:6px;cursor:pointer;border:1px solid transparent;transition:all 0.15s}}
.toggle:hover{{border-color:var(--border)}}
.toggle.on{{border-color:var(--primary);background:rgba(99,102,241,0.1)}}
.toggle-icon{{width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px}}
.toggle-icon.inside{{background:rgba(34,197,94,0.2)}}
.toggle-icon.nearby{{background:rgba(245,158,11,0.2)}}
.toggle-icon.auction{{background:rgba(59,130,246,0.2)}}
.toggle-icon.public{{background:rgba(168,85,247,0.2)}}
.toggle-icon.infra{{background:rgba(6,182,212,0.15)}}
.toggle-info{{flex:1}}
.toggle-name{{font-size:13px;font-weight:500;color:var(--text)}}
.toggle-cnt{{font-size:11px;color:var(--muted)}}
.toggle-sw{{width:40px;height:22px;background:var(--border);border-radius:11px;position:relative;transition:background 0.15s}}
.toggle-sw::after{{content:'';position:absolute;width:16px;height:16px;background:white;border-radius:50%;top:3px;left:3px;transition:transform 0.15s}}
.toggle.on .toggle-sw{{background:var(--primary)}}
.toggle.on .toggle-sw::after{{transform:translateX(18px)}}
.map-btns{{display:flex;gap:6px;margin-top:12px}}
.map-btn{{flex:1;padding:8px;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--muted);font-size:11px;cursor:pointer}}
.map-btn.on{{background:var(--primary);border-color:var(--primary);color:white}}
.legend{{position:fixed;bottom:16px;right:16px;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 14px;z-index:1000}}
.legend-title{{font-size:11px;font-weight:600;color:var(--text);margin-bottom:6px}}
.legend-item{{display:flex;align-items:center;gap:6px;font-size:10px;color:var(--muted);margin:3px 0}}
.legend-dot{{width:10px;height:10px;border-radius:50%}}
.loading{{position:fixed;top:0;left:0;right:0;bottom:0;background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:9999}}
.spinner{{width:40px;height:40px;border:3px solid var(--border);border-top-color:var(--primary);border-radius:50%;animation:spin 0.8s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.loading-txt{{margin-top:12px;color:var(--text);font-size:14px}}
</style>
</head>
<body>
<div class="loading" id="loading"><div class="spinner"></div><div class="loading-txt" id="loadingTxt">지도 로딩 중...</div></div>
<div id="map"></div>
<div class="panel">
  <div class="panel-header">
    <div class="panel-title">투자지도 PRO</div>
    <div class="panel-sub">전국 경공매 {cnt_total:,}건</div>
  </div>
  <div class="panel-body">
    <div class="stats">
      <div class="stat"><div class="stat-val">{cnt_inside + cnt_nearby:,}</div><div class="stat-lbl">사업지구 연관</div></div>
      <div class="stat"><div class="stat-val">{cnt_auction + cnt_public:,}</div><div class="stat-lbl">일반 경공매</div></div>
    </div>
    <div class="search">
      <input type="text" id="q" placeholder="주소/사건번호 검색" onkeypress="if(event.key==='Enter')doSearch()">
      <button onclick="doSearch()">검색</button>
    </div>
    <div class="section">사업지구 연관</div>
    <div class="toggle on" data-layer="inside" onclick="tog('inside')"><div class="toggle-icon inside">📍</div><div class="toggle-info"><div class="toggle-name">지구내</div><div class="toggle-cnt">{cnt_inside:,}건</div></div><div class="toggle-sw"></div></div>
    <div class="toggle on" data-layer="nearby" onclick="tog('nearby')"><div class="toggle-icon nearby">📌</div><div class="toggle-info"><div class="toggle-name">지구 인근</div><div class="toggle-cnt">{cnt_nearby:,}건</div></div><div class="toggle-sw"></div></div>
    <div class="section">일반 경공매</div>
    <div class="toggle" data-layer="auction" onclick="tog('auction')"><div class="toggle-icon auction">🔵</div><div class="toggle-info"><div class="toggle-name">경매</div><div class="toggle-cnt">{cnt_auction:,}건</div></div><div class="toggle-sw"></div></div>
    <div class="toggle" data-layer="public" onclick="tog('public')"><div class="toggle-icon public">🟣</div><div class="toggle-info"><div class="toggle-name">공매</div><div class="toggle-cnt">{cnt_public:,}건</div></div><div class="toggle-sw"></div></div>
    <div class="section">인프라</div>
    <div class="toggle" data-layer="proj" onclick="tog('proj')"><div class="toggle-icon infra">🏗️</div><div class="toggle-info"><div class="toggle-name">사업지구 경계</div><div class="toggle-cnt">172개</div></div><div class="toggle-sw"></div></div>
    <div class="toggle" data-layer="rail" onclick="tog('rail')"><div class="toggle-icon infra">🚇</div><div class="toggle-info"><div class="toggle-name">철도역</div><div class="toggle-cnt">280개</div></div><div class="toggle-sw"></div></div>
    <div class="toggle" data-layer="highway" onclick="tog('highway')"><div class="toggle-icon infra">🛣️</div><div class="toggle-info"><div class="toggle-name">고속도로 IC</div><div class="toggle-cnt">159개</div></div><div class="toggle-sw"></div></div>
    <div class="map-btns">
      <button class="map-btn on" onclick="setType('roadmap',this)">일반</button>
      <button class="map-btn" onclick="setType('skyview',this)">위성</button>
      <button class="map-btn" onclick="setType('hybrid',this)">하이브리드</button>
    </div>
  </div>
</div>
<div class="legend">
  <div class="legend-title">범례</div>
  <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div>지구내</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>지구인근</div>
  <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div>경매</div>
  <div class="legend-item"><div class="legend-dot" style="background:#a855f7"></div>공매</div>
</div>

<script>
var DATA={{inside:{inside_json},nearby:{nearby_json},auction:{auction_json},public:{public_json}}};
var projData={proj_json};
var railData={rail_json};
var highwayData={highway_json};
var COLORS={{inside:'#22c55e',nearby:'#f59e0b',auction:'#3b82f6',public:'#a855f7'}};
var map,clusterer,curPoly=null;
var markers={{inside:[],nearby:[],auction:[],public:[]}};
var layers={{proj:[],rail:[],highway:[]}};
var visible={{inside:true,nearby:true,auction:false,public:false,proj:false,rail:false,highway:false}};

function initMap(){{
  try{{
    var container=document.getElementById('map');
    map=new kakao.maps.Map(container,{{center:new kakao.maps.LatLng(36.5,127.5),level:13}});
    clusterer=new kakao.maps.MarkerClusterer({{
      map:map,averageCenter:true,minLevel:5,disableClickZoom:true,
      styles:[
        {{width:'44px',height:'44px',background:'rgba(99,102,241,0.9)',borderRadius:'50%',color:'#fff',textAlign:'center',fontWeight:'bold',lineHeight:'44px',fontSize:'13px'}},
        {{width:'54px',height:'54px',background:'rgba(99,102,241,0.9)',borderRadius:'50%',color:'#fff',textAlign:'center',fontWeight:'bold',lineHeight:'54px',fontSize:'15px'}},
        {{width:'64px',height:'64px',background:'rgba(99,102,241,0.9)',borderRadius:'50%',color:'#fff',textAlign:'center',fontWeight:'bold',lineHeight:'64px',fontSize:'17px'}}
      ]
    }});
    ['inside','nearby','auction','public'].forEach(function(type){{
      DATA[type].forEach(function(d){{
        var svg='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><circle cx="10" cy="10" r="8" fill="'+COLORS[type]+'" stroke="#fff" stroke-width="2"/></svg>');
        var img=new kakao.maps.MarkerImage(svg,new kakao.maps.Size(20,20),{{offset:new kakao.maps.Point(10,10)}});
        var m=new kakao.maps.Marker({{position:new kakao.maps.LatLng(d.lat,d.lng),image:img}});
        m._d=d;m._t=type;
        kakao.maps.event.addListener(m,'click',function(){{
          var info='<div style="padding:12px;max-width:280px;font-size:12px;line-height:1.5"><b style="font-size:14px">'+d.case_no+'</b><br><span style="color:#666">'+d.address+'</span><br><br><b>용도:</b> '+d.usage+'<br><b>감정가:</b> <span style="color:#e11d48">'+fmtPrice(d.appraisal)+'</span><br><b>최저가:</b> <span style="color:#e11d48">'+fmtPrice(d.min_price)+'</span> ('+d.ratio+')<br><b>상태:</b> '+d.status+' | '+d.date+'</div>';
          var iw=new kakao.maps.InfoWindow({{content:info,removable:true}});
          iw.open(map,m);
          showParcel(d.lat,d.lng,type);
        }});
        markers[type].push(m);
      }});
    }});
    updateClusterer();
    createInfra();
    kakao.maps.event.addListener(map,'click',function(){{if(curPoly){{curPoly.setMap(null);curPoly=null;}}}});
    document.getElementById('loading').style.display='none';
  }}catch(e){{
    document.getElementById('loadingTxt').innerHTML='<span style="color:#ef4444">오류: '+e.message+'</span>';
  }}
}}

function fmtPrice(p){{if(p>=100000000)return(p/100000000).toFixed(1)+'억';return Math.round(p/10000).toLocaleString()+'만원';}}
function updateClusterer(){{var arr=[];['inside','nearby','auction','public'].forEach(function(t){{if(visible[t])arr=arr.concat(markers[t]);}});clusterer.clear();clusterer.addMarkers(arr);}}
function tog(layer){{visible[layer]=!visible[layer];var el=document.querySelector('[data-layer="'+layer+'"]');el.classList.toggle('on',visible[layer]);if(layer==='inside'||layer==='nearby'||layer==='auction'||layer==='public'){{updateClusterer();}}else{{layers[layer].forEach(function(o){{o.setMap(visible[layer]?map:null);}});}}}}
function createInfra(){{projData.forEach(function(p){{if(!p.path||p.path.length<3)return;var path=p.path.map(function(c){{return new kakao.maps.LatLng(c[0],c[1]);}});var poly=new kakao.maps.Polygon({{path:path,strokeWeight:2,strokeColor:'#06b6d4',strokeOpacity:0.8,fillColor:'#06b6d4',fillOpacity:0.1}});layers.proj.push(poly);}});railData.forEach(function(r){{var emoji=(r.line&&(r.line.includes('호선')||r.line.includes('GTX')))?'🚇':'🚄';var svg='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><text x="10" y="15" font-size="14" text-anchor="middle">'+emoji+'</text></svg>');var m=new kakao.maps.Marker({{position:new kakao.maps.LatLng(r.lat,r.lng),image:new kakao.maps.MarkerImage(svg,new kakao.maps.Size(20,20))}});layers.rail.push(m);}});highwayData.forEach(function(h){{var svg='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="18" height="12"><rect width="18" height="12" rx="2" fill="#16a34a"/><text x="9" y="9" font-size="7" fill="#fff" text-anchor="middle" font-weight="bold">IC</text></svg>');var m=new kakao.maps.Marker({{position:new kakao.maps.LatLng(h.lat,h.lng),image:new kakao.maps.MarkerImage(svg,new kakao.maps.Size(18,12))}});layers.highway.push(m);}});}}
function showParcel(lat,lng,type){{if(curPoly){{curPoly.setMap(null);curPoly=null;}}map.setCenter(new kakao.maps.LatLng(lat,lng));if(map.getLevel()>3)map.setLevel(3);var x=lng*20037508.34/180;var y=Math.log(Math.tan((90+lat)*Math.PI/360))/(Math.PI/180)*20037508.34/180;var bbox=(x-50)+','+(y-50)+','+(x+50)+','+(y+50);fetch('/.netlify/functions/vworld?bbox='+bbox).then(function(r){{return r.json();}}).then(function(data){{if(!data.features||!data.features.length)return;var best=null,minD=Infinity;data.features.forEach(function(f){{if(!f.geometry||!f.geometry.coordinates)return;var coords=f.geometry.type==='MultiPolygon'?f.geometry.coordinates[0][0]:f.geometry.coordinates[0];if(!coords)return;var cx=0,cy=0;coords.forEach(function(c){{cx+=c[0];cy+=c[1];}});cx/=coords.length;cy/=coords.length;var d=Math.sqrt((cx-x)*(cx-x)+(cy-y)*(cy-y));if(d<minD){{minD=d;best=f;}}}});if(!best)return;var coords=best.geometry.type==='MultiPolygon'?best.geometry.coordinates[0][0]:best.geometry.coordinates[0];var path=coords.map(function(c){{var lon=c[0]*180/20037508.34;var la=Math.atan(Math.exp(c[1]*Math.PI/20037508.34))*360/Math.PI-90;return new kakao.maps.LatLng(la,lon);}});curPoly=new kakao.maps.Polygon({{path:path,strokeWeight:3,strokeColor:COLORS[type],strokeOpacity:1,fillColor:COLORS[type],fillOpacity:0.4,map:map}});}}).catch(function(e){{console.error(e);}});}}
function doSearch(){{var q=document.getElementById('q').value.toLowerCase().trim();if(!q)return;var found=null;['inside','nearby','auction','public'].some(function(t){{return DATA[t].some(function(d){{if(d.address.toLowerCase().includes(q)||d.case_no.toLowerCase().includes(q)){{found={{d:d,t:t}};return true;}}}});}});if(found){{if(!visible[found.t])tog(found.t);map.setCenter(new kakao.maps.LatLng(found.d.lat,found.d.lng));map.setLevel(3);showParcel(found.d.lat,found.d.lng,found.t);}}else{{alert('검색 결과 없음');}}}}
function setType(type,btn){{document.querySelectorAll('.map-btn').forEach(function(b){{b.classList.remove('on');}});btn.classList.add('on');var types={{roadmap:kakao.maps.MapTypeId.ROADMAP,skyview:kakao.maps.MapTypeId.SKYVIEW,hybrid:kakao.maps.MapTypeId.HYBRID}};map.setMapTypeId(types[type]);}}
</script>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=7e60f6a42602355b925c66ea6db3bd87&libraries=clusterer&autoload=false"></script>
<script>kakao.maps.load(initMap);</script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"완료! ({cnt_total:,}건)")
