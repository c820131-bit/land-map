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
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a}}
#map{{width:100%;height:100vh}}
.panel{{position:fixed;top:16px;left:16px;width:300px;max-height:calc(100vh - 32px);background:#1e293b;border-radius:16px;box-shadow:0 20px 40px rgba(0,0,0,0.4);z-index:1000;overflow:hidden;border:1px solid #334155}}
.panel-header{{padding:20px;background:linear-gradient(135deg,#6366f1 0%,#a855f7 100%);color:white}}
.panel-title{{font-size:20px;font-weight:700}}
.panel-sub{{font-size:12px;opacity:0.9;margin-top:4px}}
.panel-body{{padding:16px;max-height:calc(100vh - 160px);overflow-y:auto}}
.panel-body::-webkit-scrollbar{{width:5px}}
.panel-body::-webkit-scrollbar-thumb{{background:#334155;border-radius:3px}}
.stats{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px}}
.stat{{background:#0f172a;border-radius:10px;padding:12px;text-align:center;border:1px solid #334155}}
.stat-val{{font-size:18px;font-weight:700;color:#6366f1}}
.stat-lbl{{font-size:10px;color:#94a3b8;margin-top:2px}}
.search{{display:flex;gap:8px;margin-bottom:16px}}
.search input{{flex:1;padding:10px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:#f8fafc;font-size:13px;outline:none}}
.search input:focus{{border-color:#6366f1}}
.search button{{padding:10px 14px;background:#6366f1;color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer}}
.section{{font-size:10px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin:14px 0 8px}}
.chk-row{{display:flex;align-items:center;gap:10px;padding:8px 10px;background:#0f172a;border-radius:8px;margin-bottom:4px;cursor:pointer}}
.chk-row:hover{{background:#1e293b}}
.chk-row input{{width:16px;height:16px;accent-color:#6366f1}}
.chk-row label{{flex:1;font-size:13px;color:#f8fafc;cursor:pointer}}
.chk-row .cnt{{font-size:11px;color:#94a3b8}}
.map-btns{{display:flex;gap:6px;margin-top:12px}}
.map-btn{{flex:1;padding:8px;background:#0f172a;border:1px solid #334155;border-radius:6px;color:#94a3b8;font-size:11px;cursor:pointer}}
.map-btn.on{{background:#6366f1;border-color:#6366f1;color:white}}
.legend{{position:fixed;bottom:16px;right:16px;background:#1e293b;border:1px solid #334155;border-radius:10px;padding:10px 14px;z-index:1000}}
.legend-title{{font-size:11px;font-weight:600;color:#f8fafc;margin-bottom:6px}}
.legend-item{{display:flex;align-items:center;gap:6px;font-size:10px;color:#94a3b8;margin:3px 0}}
.legend-dot{{width:10px;height:10px;border-radius:50%}}
</style>
</head>
<body>
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
      <input type="text" id="searchInput" placeholder="주소/사건번호 검색">
      <button onclick="search()">검색</button>
    </div>
    <div class="section">사업지구 연관</div>
    <div class="chk-row"><input type="checkbox" id="chkInside" checked onchange="toggle('inside')"><label for="chkInside">📍 지구내</label><span class="cnt">{cnt_inside:,}건</span></div>
    <div class="chk-row"><input type="checkbox" id="chkNearby" checked onchange="toggle('nearby')"><label for="chkNearby">📌 지구 인근</label><span class="cnt">{cnt_nearby:,}건</span></div>
    <div class="section">일반 경공매</div>
    <div class="chk-row"><input type="checkbox" id="chkAuction" onchange="toggle('auction')"><label for="chkAuction">🔵 경매</label><span class="cnt">{cnt_auction:,}건</span></div>
    <div class="chk-row"><input type="checkbox" id="chkPublic" onchange="toggle('public')"><label for="chkPublic">🟣 공매</label><span class="cnt">{cnt_public:,}건</span></div>
    <div class="section">인프라</div>
    <div class="chk-row"><input type="checkbox" id="chkProj" onchange="toggle('proj')"><label for="chkProj">🏗️ 사업지구 경계</label><span class="cnt">172개</span></div>
    <div class="chk-row"><input type="checkbox" id="chkRail" onchange="toggle('rail')"><label for="chkRail">🚇 철도역</label><span class="cnt">280개</span></div>
    <div class="chk-row"><input type="checkbox" id="chkHighway" onchange="toggle('highway')"><label for="chkHighway">🛣️ 고속도로 IC</label><span class="cnt">159개</span></div>
    <div class="map-btns">
      <button class="map-btn on" onclick="setMapType('roadmap',this)">일반</button>
      <button class="map-btn" onclick="setMapType('skyview',this)">위성</button>
      <button class="map-btn" onclick="setMapType('hybrid',this)">하이브리드</button>
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

function init(){{
  var container=document.getElementById('map');
  map=new kakao.maps.Map(container,{{center:new kakao.maps.LatLng(36.5,127.5),level:13}});

  clusterer=new kakao.maps.MarkerClusterer({{
    map:map,
    averageCenter:true,
    minLevel:5,
    disableClickZoom:true,
    styles:[
      {{width:'44px',height:'44px',background:'rgba(99,102,241,0.9)',borderRadius:'50%',color:'#fff',textAlign:'center',fontWeight:'bold',lineHeight:'44px',fontSize:'13px'}},
      {{width:'54px',height:'54px',background:'rgba(99,102,241,0.9)',borderRadius:'50%',color:'#fff',textAlign:'center',fontWeight:'bold',lineHeight:'54px',fontSize:'15px'}}
    ]
  }});

  ['inside','nearby','auction','public'].forEach(function(type){{
    DATA[type].forEach(function(d){{
      var svg='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><circle cx="10" cy="10" r="8" fill="'+COLORS[type]+'" stroke="#fff" stroke-width="2"/></svg>');
      var img=new kakao.maps.MarkerImage(svg,new kakao.maps.Size(20,20),{{offset:new kakao.maps.Point(10,10)}});
      var m=new kakao.maps.Marker({{position:new kakao.maps.LatLng(d.lat,d.lng),image:img}});
      m._d=d;m._t=type;
      kakao.maps.event.addListener(m,'click',function(){{
        var c='<div style="padding:12px;max-width:280px;font-size:12px;line-height:1.5"><b style="font-size:14px">'+d.case_no+'</b><br><span style="color:#666">'+d.address+'</span><br><br>용도: '+d.usage+'<br>감정가: <b style="color:#e11d48">'+fmtPrice(d.appraisal)+'</b><br>최저가: <b style="color:#e11d48">'+fmtPrice(d.min_price)+'</b> ('+d.ratio+')<br>'+d.status+' | '+d.date+'</div>';
        new kakao.maps.InfoWindow({{content:c,removable:true}}).open(map,m);
        showParcel(d.lat,d.lng,type);
      }});
      markers[type].push(m);
    }});
  }});

  updateClusterer();
  createInfra();

  kakao.maps.event.addListener(map,'click',function(){{
    if(curPoly){{curPoly.setMap(null);curPoly=null;}}
  }});
}}

function fmtPrice(p){{
  if(p>=100000000)return(p/100000000).toFixed(1)+'억';
  return Math.round(p/10000).toLocaleString()+'만원';
}}

function updateClusterer(){{
  var arr=[];
  ['inside','nearby','auction','public'].forEach(function(t){{
    if(visible[t])arr=arr.concat(markers[t]);
  }});
  clusterer.clear();
  clusterer.addMarkers(arr);
}}

function toggle(layer){{
  var chk=document.getElementById('chk'+layer.charAt(0).toUpperCase()+layer.slice(1));
  visible[layer]=chk.checked;
  if(layer==='inside'||layer==='nearby'||layer==='auction'||layer==='public'){{
    updateClusterer();
  }}else{{
    layers[layer].forEach(function(o){{o.setMap(visible[layer]?map:null);}});
  }}
}}

function createInfra(){{
  projData.forEach(function(p){{
    if(!p.path||p.path.length<3)return;
    var path=p.path.map(function(c){{return new kakao.maps.LatLng(c[0],c[1]);}});
    var poly=new kakao.maps.Polygon({{path:path,strokeWeight:2,strokeColor:'#06b6d4',strokeOpacity:0.8,fillColor:'#06b6d4',fillOpacity:0.1}});
    layers.proj.push(poly);
  }});
  railData.forEach(function(r){{
    var emoji=(r.line&&(r.line.includes('호선')||r.line.includes('GTX')))?'🚇':'🚄';
    var svg='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><text x="10" y="15" font-size="14" text-anchor="middle">'+emoji+'</text></svg>');
    var m=new kakao.maps.Marker({{position:new kakao.maps.LatLng(r.lat,r.lng),image:new kakao.maps.MarkerImage(svg,new kakao.maps.Size(20,20))}});
    layers.rail.push(m);
  }});
  highwayData.forEach(function(h){{
    var svg='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="18" height="12"><rect width="18" height="12" rx="2" fill="#16a34a"/><text x="9" y="9" font-size="7" fill="#fff" text-anchor="middle" font-weight="bold">IC</text></svg>');
    var m=new kakao.maps.Marker({{position:new kakao.maps.LatLng(h.lat,h.lng),image:new kakao.maps.MarkerImage(svg,new kakao.maps.Size(18,12))}});
    layers.highway.push(m);
  }});
}}

function showParcel(lat,lng,type){{
  if(curPoly){{curPoly.setMap(null);curPoly=null;}}
  map.setCenter(new kakao.maps.LatLng(lat,lng));
  if(map.getLevel()>3)map.setLevel(3);
  var x=lng*20037508.34/180;
  var y=Math.log(Math.tan((90+lat)*Math.PI/360))/(Math.PI/180)*20037508.34/180;
  var bbox=(x-50)+','+(y-50)+','+(x+50)+','+(y+50);
  fetch('/.netlify/functions/vworld?bbox='+bbox).then(function(r){{return r.json();}}).then(function(data){{
    if(!data.features||!data.features.length)return;
    var best=null,minD=Infinity;
    data.features.forEach(function(f){{
      if(!f.geometry||!f.geometry.coordinates)return;
      var coords=f.geometry.type==='MultiPolygon'?f.geometry.coordinates[0][0]:f.geometry.coordinates[0];
      if(!coords)return;
      var cx=0,cy=0;
      coords.forEach(function(c){{cx+=c[0];cy+=c[1];}});
      cx/=coords.length;cy/=coords.length;
      var d=Math.sqrt((cx-x)*(cx-x)+(cy-y)*(cy-y));
      if(d<minD){{minD=d;best=f;}}
    }});
    if(!best)return;
    var coords=best.geometry.type==='MultiPolygon'?best.geometry.coordinates[0][0]:best.geometry.coordinates[0];
    var path=coords.map(function(c){{
      var lon=c[0]*180/20037508.34;
      var la=Math.atan(Math.exp(c[1]*Math.PI/20037508.34))*360/Math.PI-90;
      return new kakao.maps.LatLng(la,lon);
    }});
    curPoly=new kakao.maps.Polygon({{path:path,strokeWeight:3,strokeColor:COLORS[type],strokeOpacity:1,fillColor:COLORS[type],fillOpacity:0.4,map:map}});
  }}).catch(function(e){{console.error(e);}});
}}

function search(){{
  var q=document.getElementById('searchInput').value.toLowerCase().trim();
  if(!q)return;
  var found=null;
  ['inside','nearby','auction','public'].some(function(t){{
    return DATA[t].some(function(d){{
      if(d.address.toLowerCase().includes(q)||d.case_no.toLowerCase().includes(q)){{
        found={{d:d,t:t}};return true;
      }}
    }});
  }});
  if(found){{
    if(!visible[found.t]){{
      document.getElementById('chk'+found.t.charAt(0).toUpperCase()+found.t.slice(1)).checked=true;
      toggle(found.t);
    }}
    map.setCenter(new kakao.maps.LatLng(found.d.lat,found.d.lng));
    map.setLevel(3);
    showParcel(found.d.lat,found.d.lng,found.t);
  }}else{{alert('검색 결과 없음');}}
}}

function setMapType(type,btn){{
  document.querySelectorAll('.map-btn').forEach(function(b){{b.classList.remove('on');}});
  btn.classList.add('on');
  var types={{roadmap:kakao.maps.MapTypeId.ROADMAP,skyview:kakao.maps.MapTypeId.SKYVIEW,hybrid:kakao.maps.MapTypeId.HYBRID}};
  map.setMapTypeId(types[type]);
}}

document.getElementById('searchInput').addEventListener('keypress',function(e){{if(e.key==='Enter')search();}});
</script>
<script>
(function(){{
  var s=document.createElement('script');
  s.src='https://dapi.kakao.com/v2/maps/sdk.js?appkey=7e60f6a42602355b925c66ea6db3bd87&libraries=clusterer&autoload=false';
  s.onload=function(){{kakao.maps.load(init);}};
  document.head.appendChild(s);
}})();
</script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"완료! ({cnt_total:,}건)")
