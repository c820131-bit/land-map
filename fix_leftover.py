# -*- coding: utf-8 -*-

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 잔여 코드 제거
leftover = '''
// 클릭 위치에 원 표시
var col=type==='inside'?'#4CAF50':type==='nearby'?'#FF9800':type==='auction'?'#2196F3':type==='public'?'#9C27B0':'#9E9E9E';
curPoly=new kakao.maps.Circle({
center:new kakao.maps.LatLng(lat,lng),
radius:15,
strokeWeight:3,
strokeColor:col,
strokeOpacity:1,
fillColor:col,
fillOpacity:0.3,
map:map
});
}

'''

content = content.replace(leftover, '\n')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("잔여 코드 제거 완료!")
