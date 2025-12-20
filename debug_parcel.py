# -*- coding: utf-8 -*-

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 기존 showParcel 함수를 더 자세한 디버깅이 포함된 버전으로 교체
old_showParcel = '''function showParcel(lat,lng,type){
if(curPoly){curPoly.setMap(null);curPoly=null;}
map.setCenter(new kakao.maps.LatLng(lat,lng));
map.setLevel(1);

var x=lng*20037508.34/180;
var y=Math.log(Math.tan((90+lat)*Math.PI/360))/(Math.PI/180)*20037508.34/180;
var bbox=(x-50)+','+(y-50)+','+(x+50)+','+(y+50);
var url='https://api.vworld.kr/req/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=lp_pa_cbnd_bubun&BBOX='+bbox+'&SRSNAME=EPSG:900913&OUTPUT=application/json&KEY='+VWORLD_KEY+'&DOMAIN=c820131-bit.github.io';

fetch(url).then(function(r){
if(!r.ok){console.log('API 응답 오류:',r.status);return null;}
return r.json();
}).then(function(d){
if(!d){console.log('응답 없음');return;}
if(!d.features||!d.features.length){console.log('필지 데이터 없음, 좌표:',lat,lng);alert('해당 위치의 필지 정보를 찾을 수 없습니다.');return;}
console.log('필지 데이터 수신:',d.features.length,'개');

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

if(!best)return;

var coords=best.geometry.type==='MultiPolygon'?best.geometry.coordinates[0][0]:best.geometry.coordinates[0];
console.log('좌표 개수:',coords.length,'geometry 타입:',best.geometry.type);
var path=coords.map(function(c){
var lon=c[0]*180/20037508.34;
var la=Math.atan(Math.exp(c[1]*Math.PI/20037508.34))*360/Math.PI-90;
return new kakao.maps.LatLng(la,lon);
});

var col=type==='inside'?'#4CAF50':type==='nearby'?'#FF9800':type==='auction'?'#2196F3':type==='public'?'#9C27B0':'#9E9E9E';
console.log('폴리곤 생성, 꼭지점 수:',path.length);
curPoly=new kakao.maps.Polygon({
path:path,
strokeWeight:4,
strokeColor:'#000',
strokeOpacity:1,
fillColor:col,
fillOpacity:0.6,
map:map
});
}).catch(function(e){console.log('API error:',e);});
}'''

new_showParcel = '''function showParcel(lat,lng,type){
alert('1. showParcel 호출됨: '+lat+', '+lng+', '+type);
if(curPoly){curPoly.setMap(null);curPoly=null;}
map.setCenter(new kakao.maps.LatLng(lat,lng));
map.setLevel(1);

var x=lng*20037508.34/180;
var y=Math.log(Math.tan((90+lat)*Math.PI/360))/(Math.PI/180)*20037508.34/180;
var bbox=(x-50)+','+(y-50)+','+(x+50)+','+(y+50);
var url='https://api.vworld.kr/req/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=lp_pa_cbnd_bubun&BBOX='+bbox+'&SRSNAME=EPSG:900913&OUTPUT=application/json&KEY='+VWORLD_KEY+'&DOMAIN=c820131-bit.github.io';

alert('2. API 호출 시작');
fetch(url).then(function(r){
alert('3. API 응답 받음, status: '+r.status);
if(!r.ok){alert('API 오류: '+r.status);return null;}
return r.json();
}).then(function(d){
if(!d){alert('4. 응답 데이터 없음');return;}
alert('4. 필지 데이터 수신: '+(d.features?d.features.length:0)+'개');
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

if(!best){alert('5. 가장 가까운 필지 없음');return;}

var coords=best.geometry.type==='MultiPolygon'?best.geometry.coordinates[0][0]:best.geometry.coordinates[0];
alert('5. 폴리곤 생성: '+coords.length+'개 꼭지점, 타입: '+best.geometry.type);
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
fillOpacity:0.6,
map:map
});
alert('6. 폴리곤 생성 완료!');
}).catch(function(e){alert('API 에러: '+e.message);});
}'''

content = content.replace(old_showParcel, new_showParcel)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("완료! 디버깅용 alert 추가됨")
print("마커 클릭 시 각 단계별 alert가 표시됩니다")
