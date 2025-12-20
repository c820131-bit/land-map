# -*- coding: utf-8 -*-
import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 현재 showParcel 함수를 찾아서 Vworld API 직접 호출 방식으로 교체
old_pattern = r"function showParcel\(lat,lng,type\)\{[\s\S]*?\n\}"

new_func = '''function showParcel(lat,lng,type){
if(curPoly){curPoly.setMap(null);curPoly=null;}
map.setCenter(new kakao.maps.LatLng(lat,lng));
map.setLevel(1);

var x=lng*20037508.34/180;
var y=Math.log(Math.tan((90+lat)*Math.PI/360))/(Math.PI/180)*20037508.34/180;
var bbox=(x-50)+','+(y-50)+','+(x+50)+','+(y+50);
var url='https://api.vworld.kr/req/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=lp_pa_cbnd_bubun&BBOX='+bbox+'&SRSNAME=EPSG:900913&OUTPUT=application/json&KEY='+VWORLD_KEY+'&DOMAIN=c820131-bit.github.io';

fetch(url).then(function(r){
if(!r.ok)throw new Error('API오류:'+r.status);
return r.json();
}).then(function(d){
if(!d.features||!d.features.length){alert('필지 정보 없음');return;}

var best=null,minD=Infinity;
d.features.forEach(function(f){
if(!f.geometry||!f.geometry.coordinates)return;
var cs=f.geometry.type==='MultiPolygon'?f.geometry.coordinates[0][0]:f.geometry.coordinates[0];
if(!cs||!cs.length)return;
var cx=0,cy=0;
cs.forEach(function(c){cx+=c[0];cy+=c[1];});
cx/=cs.length;cy/=cs.length;
var dist=Math.sqrt((cx-x)*(cx-x)+(cy-y)*(cy-y));
if(dist<minD){minD=dist;best=f;}
});

if(!best){alert('필지 못찾음');return;}

var coords=best.geometry.type==='MultiPolygon'?best.geometry.coordinates[0][0]:best.geometry.coordinates[0];
var path=coords.map(function(c){
var lon=c[0]*180/20037508.34;
var la=Math.atan(Math.exp(c[1]*Math.PI/20037508.34))*360/Math.PI-90;
return new kakao.maps.LatLng(la,lon);
});

var col=type==='inside'?'#4CAF50':type==='nearby'?'#FF9800':type==='auction'?'#2196F3':type==='public'?'#9C27B0':'#9E9E9E';
curPoly=new kakao.maps.Polygon({
path:path,
strokeWeight:4,
strokeColor:'#000',
strokeOpacity:1,
fillColor:col,
fillOpacity:0.5,
map:map
});
}).catch(function(e){alert('오류:'+e.message);});
}'''

content = re.sub(old_pattern, new_func, content, count=1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("완료! Vworld API 직접 호출 방식으로 복구")
