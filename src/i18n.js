// 화면 문구 7개 언어 + 한글 지명·상호 로마자 변환 (국어의 로마자 표기법을 단순화)
window.LANGS = [["ko", "한국어"], ["en", "English"], ["pt", "Português"], ["ru", "Русский"], ["ja", "日本語"], ["zh", "中文"], ["hi", "हिन्दी"]];
window.LOCALE = { ko: "ko-KR", en: "en-US", pt: "pt-BR", ru: "ru-RU", ja: "ja-JP", zh: "zh-CN", hi: "hi-IN" };

window.I18N = {
ko: {
  title: "편의점에서 가장 먼 곳",
  h1: '편의점에서 <span class="far">가장 먼</span> 곳',
  lede: "대한민국에서 편의점과 가장 멀리 떨어질 수 있는 곳은 어디일까요",
  lang: "언어",
  a_stage: "반지름을 키우는 지도", a_map: "편의점마다 같은 반지름의 원을 그린 지도", a_brands: "편의점 브랜드",
  a_slider: "반지름", a_region: "범위", a_zoom: "최원점 주변 확대", a_chart: "반지름에 따른 덮인 비율", close: "닫기",
  recenter: "자동 시점", credit: "배경지도 © Esri · 지명 통계청",
  b_all: "전체", b_gs: "GS25", b_cu: "CU", b_se: "세븐일레븐", b_e24: "이마트24",
  stores: "편의점", store_word: "편의점",
  cover: "국토의 {cov}가 이 거리 안에 편의점이 있습니다", pairs: "서로 겹친 원 {pairs}쌍",
  play: "재생", pause: "멈춤",
  seg_south: "DMZ 밖 본토", seg_mainland: "DMZ 포함", seg_all: "섬 포함",
  hint: "지도는 끌어서 옮기고 휠이나 두 손가락, 더블클릭으로 확대합니다. 점을 누르면 편의점 이름이, 빈 곳을 누르면 가장 가까운 편의점이 나옵니다",
  ans_all: "전체 편의점", ans_only: "{b}만", dist_sub: "가장 가까운 편의점까지 직선거리",
  note_vertex: "세 편의점에서 똑같이 떨어진 한 점", note_coast: "해안선 위 한 점", note_dmz: "군사분계선 위, 비무장지대 안",
  dokdo: " · 독도는 {d} km",
  kind_vertex: "세 원이 한 점에서 만나는 외심이 답입니다.", kind_coast: "답이 육지 안 외심이 아니라 경계선 위에 있습니다.",
  rstar: "이 범위의 답 {r}. {kind}", half: "반지름 {h}면 국토의 절반, 10 km면 {c}가 덮입니다.",
  live_pairs: "지금 반지름에서 서로 겹친 원 {pairs2}쌍 · 교차점 {pts2}개", live_tri: "전국 편의점으로 만든 들로네 삼각형 {nv2}개, 외심 후보도 같은 수",
  nation: "전국", more: "외 {n}곳", here1: "이 자리 편의점", hereN: "이 자리 편의점 {n}곳", near: "여기서 가장 가까운 {b}", straight: "직선거리",
  h2_math: "계산에 쓴 공식",
  eq1_h: "두 점 사이 거리", eq1_p: "지구를 반지름 6,371 km 구로 보고 대원거리를 씁니다. 실제 계산은 두 점을 단위벡터로 바꿔 현의 길이 c를 구한 뒤 거리로 되돌립니다.",
  eq2_h: "두 원이 만나는 조건과 교차점", eq2_p: "반지름이 r인 두 원은 중심 사이 거리 ℓ이 2r 이하일 때 만납니다. 교차점은 두 중심의 수직이등분선 위에 있고, r이 커질수록 그 선을 따라 바깥으로 미끄러집니다.",
  eq3_h: "원과 원이 맞닿는 선 = 보로노이 경계", eq3_p: "지도에서 노란 선은 두 원이 처음 만난 뒤 계속 맞닿아 있는 자리입니다. 그 선 위의 점은 두 편의점에서 거리가 같습니다. 각 편의점이 가장 가까운 영역을 나누는 경계와 같습니다.",
  eq4_h: "세 원이 한 점에서 만날 때 = 외심", eq4_p: "세 원이 동시에 한 점에서 만나는 순간의 그 점이 보로노이 꼭짓점이고, 세 편의점이 이루는 삼각형의 외심입니다. 구 위에서는 세 단위벡터로 만든 평면의 법선 방향이 곧 외심입니다.",
  eq5_h: "덮인 비율", eq5_p: "국토 L 가운데 어느 편의점의 원 안에라도 들어간 넓이의 비율입니다.",
  eq6_h: "가장 먼 곳", eq6_p: "모든 지점에서 가장 가까운 편의점까지의 거리를 재고, 그 값이 가장 큰 지점을 고릅니다. 원을 키울 때 마지막까지 덮이지 않고 남는 한 점이 바로 이 점이고, 그때의 반지름이 답입니다. 후보는 육지 안의 외심과 해안선 위의 점 두 종류뿐입니다.",
  h2_make: "만든 방법",
  mk1: "소상공인시장진흥공단 상가정보 2026년 6월판 전국 파일에서 업종이 편의점인 54,446곳을 뽑았습니다. 같은 좌표를 합치면 49,244곳입니다.",
  mk2: "통계청 2013년 시도 경계를 합쳐 섬 2,021개를 포함한 국토 폴리곤을 만들었습니다. DMZ 밖 본토는 Natural Earth의 DMZ 남방한계선 북쪽을 잘라냈습니다.",
  mk3: "편의점 좌표를 단위구 위의 벡터로 바꾸고 볼록껍질을 구했습니다. 껍질의 삼각형 면 하나가 구면 들로네 삼각형 하나이고, 면의 법선이 외심입니다. 0.3초 걸립니다.",
  mk4: "육지 안에 있는 외심 9만여 개와 해안선을 20 m 간격으로 찍은 점 30만여 개를 KD트리로 가장 가까운 편의점과 대조해 최댓값을 골랐습니다.",
  mk5: "덮인 비율은 국토를 약 550 m 격자 135만 칸으로 나눠 각 칸의 거리를 구한 뒤 넓이 가중으로 누적했습니다.",
  lim_h: "한계",
  lim1: "상가정보의 업종 분류를 그대로 따랐습니다. 농협 지소처럼 편의점으로 분류된 매장도 포함되고, 등록되지 않은 매장은 빠집니다. 흑산도에는 편의점으로 분류된 매장이 없어서 가거도의 최근접이 진도가 됐습니다.",
  lim2: "경계가 2013년 기준이라 그 뒤 생긴 매립지는 반영되지 않았습니다.",
  lim3: "모든 거리는 직선 대원거리입니다. 산길로 걸으면 훨씬 멉니다.",
  foot: "편의점 위치: 소상공인시장진흥공단 상가정보 2026-06 · 경계: 통계청 2013 · DMZ: Natural Earth · 배경지도: Esri World Dark Gray · 지명: 통계청 행정구역 2013 · 착안: everything.in.math의 McFarthest point · Claude로 만든 취미 프로젝트",
},
en: {
  title: "The Farthest Point from a Convenience Store",
  h1: 'The <span class="far">farthest</span> point from a convenience store',
  lede: "South Korea has 54,446 convenience stores. How far from one can you get?",
  lang: "Language",
  a_stage: "Map of growing circles", a_map: "Map with a circle of the same radius around every store", a_brands: "Store brand",
  a_slider: "Radius", a_region: "Region", a_zoom: "Close-up of the farthest point", a_chart: "Coverage by radius", close: "Close",
  recenter: "Auto view", credit: "Base map © Esri · Place names Statistics Korea",
  b_all: "All", b_gs: "GS25", b_cu: "CU", b_se: "7-Eleven", b_e24: "emart24",
  stores: "Stores", store_word: "store",
  cover: "{cov} of the land has a store within this distance", pairs: "{pairs} pairs of overlapping circles",
  play: "Play", pause: "Pause",
  seg_south: "Mainland, no DMZ", seg_mainland: "With DMZ", seg_all: "With islands",
  hint: "Drag to move. Use the wheel, two fingers or a double-click to zoom. Tap a dot for the store name, or an empty spot for the nearest store.",
  ans_all: "all stores", ans_only: "{b} only", dist_sub: "straight-line distance to the nearest store",
  note_vertex: "A point exactly as far from three stores", note_coast: "A point on the coastline", note_dmz: "On the Military Demarcation Line, inside the DMZ",
  dokdo: " · Dokdo: {d} km",
  kind_vertex: "The answer is the circumcenter where three circles meet.", kind_coast: "Here the answer lies on the boundary, not at a circumcenter on land.",
  rstar: "Answer for this region: {r}. {kind}", half: "A radius of {h} covers half the land, and 10 km covers {c}.",
  live_pairs: "At this radius: {pairs2} overlapping pairs · {pts2} intersection points", live_tri: "{nv2} Delaunay triangles from these stores, and as many circumcenter candidates",
  nation: "Whole country", more: "+{n} more", here1: "Store at this spot", hereN: "{n} stores at this spot", near: "Nearest {b} from here", straight: "straight line",
  h2_math: "The math",
  eq1_h: "Distance between two points", eq1_p: "The Earth is treated as a sphere with a radius of 6,371 km, and distances are great-circle distances. In practice each point becomes a unit vector, and the chord length c between two of them is turned back into a distance.",
  eq2_h: "When two circles meet, and where", eq2_p: "Two circles of radius r meet when the distance ℓ between their centers is at most 2r. The intersection points lie on the perpendicular bisector of the centers and slide outward along it as r grows.",
  eq3_h: "Where circles touch = Voronoi edges", eq3_p: "The yellow lines on the map are where two circles keep touching after they first meet. Every point on such a line is equally far from two stores, so the lines split the land into the area closest to each store.",
  eq4_h: "Three circles meeting at one point = circumcenter", eq4_p: "The point where three circles meet at the same moment is a Voronoi vertex, the circumcenter of the triangle formed by the three stores. On a sphere, the normal of the plane through the three unit vectors points to the circumcenter.",
  eq5_h: "Coverage", eq5_p: "The share of the land L that lies inside at least one store's circle.",
  eq6_h: "The farthest point", eq6_p: "Measure the distance from every point to its nearest store and pick the point where it is largest. As the circles grow, it is the last point left uncovered, and the radius at that moment is the answer. Only two kinds of candidates exist: circumcenters on land and points on the coastline.",
  h2_make: "How it was made",
  mk1: "The 54,446 businesses classified as convenience stores were taken from the June 2026 nationwide commercial district file of the Small Enterprise and Market Service. Merging identical coordinates leaves 49,244 points.",
  mk2: "Statistics Korea's 2013 province boundaries were merged into one land polygon with 2,021 islands. For the mainland outside the DMZ, everything north of Natural Earth's DMZ southern limit line was cut off.",
  mk3: "Store coordinates were turned into vectors on the unit sphere and their convex hull was computed. Each triangular face of the hull is one spherical Delaunay triangle, and its normal is a circumcenter. This takes 0.3 seconds.",
  mk4: "About 90,000 circumcenters on land and over 300,000 points sampled every 20 m along the coastline were checked against their nearest store with a KD-tree, and the largest distance was chosen.",
  mk5: "Coverage splits the land into 1.35 million cells of about 550 m, finds each cell's distance and adds them up weighted by area.",
  lim_h: "Limitations",
  lim1: "The business categories in the source data are used as is. Some other shops classified as convenience stores are included, and unregistered stores are missing. Heuksando has no shop classified as a convenience store, so Gageodo's nearest store is on Jindo.",
  lim2: "Boundaries are from 2013, so land reclaimed since then is not included.",
  lim3: "All distances are straight great-circle lines. On foot over the mountains it is much farther.",
  foot: "Stores: Small Enterprise and Market Service, June 2026 · Boundaries: Statistics Korea 2013 · DMZ: Natural Earth · Base map: Esri World Dark Gray · Inspired by the McFarthest point by everything.in.math · A hobby project built with Claude",
},
pt: {
  title: "O ponto mais distante de uma loja de conveniência",
  h1: 'O ponto <span class="far">mais distante</span> de uma loja de conveniência',
  lede: "A Coreia do Sul tem 54.446 lojas de conveniência. Até onde dá para se afastar de uma?",
  lang: "Idioma",
  a_stage: "Mapa de círculos que crescem", a_map: "Mapa com um círculo de mesmo raio em volta de cada loja", a_brands: "Marca da loja",
  a_slider: "Raio", a_region: "Região", a_zoom: "Ampliação do ponto mais distante", a_chart: "Cobertura por raio", close: "Fechar",
  recenter: "Visão automática", credit: "Mapa base © Esri · Nomes Statistics Korea",
  b_all: "Todas", b_gs: "GS25", b_cu: "CU", b_se: "7-Eleven", b_e24: "emart24",
  stores: "Lojas", store_word: "loja",
  cover: "{cov} do território tem uma loja a esta distância", pairs: "{pairs} pares de círculos sobrepostos",
  play: "Reproduzir", pause: "Pausar",
  seg_south: "Continente sem DMZ", seg_mainland: "Com DMZ", seg_all: "Com ilhas",
  hint: "Arraste para mover. Use a roda, dois dedos ou clique duplo para ampliar. Toque num ponto para ver o nome da loja, ou num lugar vazio para ver a loja mais próxima.",
  ans_all: "todas as lojas", ans_only: "só {b}", dist_sub: "distância em linha reta até a loja mais próxima",
  note_vertex: "Um ponto à mesma distância de três lojas", note_coast: "Um ponto no litoral", note_dmz: "Na Linha de Demarcação Militar, dentro da DMZ",
  dokdo: " · Dokdo: {d} km",
  kind_vertex: "A resposta é o circuncentro, onde três círculos se encontram.", kind_coast: "Aqui a resposta está na borda, não num circuncentro em terra.",
  rstar: "Resposta para esta região: {r}. {kind}", half: "Um raio de {h} cobre metade do território, e 10 km cobrem {c}.",
  live_pairs: "Neste raio: {pairs2} pares sobrepostos · {pts2} pontos de interseção", live_tri: "{nv2} triângulos de Delaunay a partir destas lojas, e o mesmo número de candidatos a circuncentro",
  nation: "País inteiro", more: "+{n}", here1: "Loja neste ponto", hereN: "{n} lojas neste ponto", near: "{b} mais próxima daqui", straight: "em linha reta",
  h2_math: "A matemática",
  eq1_h: "Distância entre dois pontos", eq1_p: "A Terra é tratada como uma esfera de raio 6.371 km, e as distâncias são de círculo máximo. Na prática, cada ponto vira um vetor unitário, e o comprimento da corda c entre dois deles é convertido de volta em distância.",
  eq2_h: "Quando dois círculos se encontram, e onde", eq2_p: "Dois círculos de raio r se encontram quando a distância ℓ entre os centros é no máximo 2r. Os pontos de interseção ficam na mediatriz dos centros e deslizam para fora ao longo dela à medida que r cresce.",
  eq3_h: "Onde os círculos se tocam = arestas de Voronoi", eq3_p: "As linhas amarelas no mapa são onde dois círculos continuam se tocando depois do primeiro encontro. Cada ponto dessas linhas fica à mesma distância de duas lojas, então elas dividem o território na área mais próxima de cada loja.",
  eq4_h: "Três círculos num só ponto = circuncentro", eq4_p: "O ponto onde três círculos se encontram ao mesmo tempo é um vértice de Voronoi, o circuncentro do triângulo formado pelas três lojas. Na esfera, a normal do plano que passa pelos três vetores unitários aponta para o circuncentro.",
  eq5_h: "Cobertura", eq5_p: "A fração do território L que fica dentro do círculo de pelo menos uma loja.",
  eq6_h: "O ponto mais distante", eq6_p: "Mede-se a distância de cada ponto até a loja mais próxima e escolhe-se o ponto onde ela é maior. Com os círculos crescendo, é o último ponto a ser coberto, e o raio nesse momento é a resposta. Só existem dois tipos de candidatos: circuncentros em terra e pontos no litoral.",
  h2_make: "Como foi feito",
  mk1: "Do arquivo nacional de comércio de junho de 2026 da Small Enterprise and Market Service foram extraídos os 54.446 estabelecimentos classificados como lojas de conveniência. Unindo coordenadas iguais, restam 49.244 pontos.",
  mk2: "Os limites provinciais de 2013 da Statistics Korea foram unidos num único polígono de terra com 2.021 ilhas. Para o continente sem DMZ, tudo ao norte da linha limite sul da DMZ da Natural Earth foi cortado.",
  mk3: "As coordenadas das lojas viraram vetores na esfera unitária, e foi calculado o fecho convexo. Cada face triangular é um triângulo de Delaunay esférico, e sua normal é um circuncentro. Leva 0,3 segundo.",
  mk4: "Cerca de 90 mil circuncentros em terra e mais de 300 mil pontos tomados a cada 20 m do litoral foram comparados com a loja mais próxima numa árvore KD, e escolheu-se a maior distância.",
  mk5: "A cobertura divide o território em 1,35 milhão de células de cerca de 550 m, calcula a distância de cada uma e soma ponderando pela área.",
  lim_h: "Limitações",
  lim1: "As categorias de negócio da fonte são usadas como estão. Algumas outras lojas classificadas como de conveniência entram, e lojas não registradas ficam de fora. Heuksando não tem loja classificada como de conveniência, então a mais próxima de Gageodo fica em Jindo.",
  lim2: "Os limites são de 2013, então terras aterradas depois disso não estão incluídas.",
  lim3: "Todas as distâncias são em linha reta. A pé pelas montanhas é bem mais longe.",
  foot: "Lojas: Small Enterprise and Market Service, junho de 2026 · Limites: Statistics Korea 2013 · DMZ: Natural Earth · Mapa base: Esri World Dark Gray · Inspirado no McFarthest point de everything.in.math · Projeto pessoal feito com Claude",
},
ru: {
  title: "Самая дальняя точка от магазина у дома",
  h1: 'Самая <span class="far">дальняя</span> точка от магазина у дома',
  lede: "В Южной Корее 54 446 магазинов у дома. Как далеко от них можно уйти?",
  lang: "Язык",
  a_stage: "Карта растущих кругов", a_map: "Карта с кругом одного радиуса вокруг каждого магазина", a_brands: "Сеть магазинов",
  a_slider: "Радиус", a_region: "Область", a_zoom: "Крупный план самой дальней точки", a_chart: "Покрытие в зависимости от радиуса", close: "Закрыть",
  recenter: "Авто-вид", credit: "Подложка © Esri · Названия Statistics Korea",
  b_all: "Все", b_gs: "GS25", b_cu: "CU", b_se: "7-Eleven", b_e24: "emart24",
  stores: "Магазины", store_word: "магазин",
  cover: "{cov} территории — магазин в пределах этого расстояния", pairs: "Пересекающихся пар кругов: {pairs}",
  play: "Пуск", pause: "Пауза",
  seg_south: "Материк без ДМЗ", seg_mainland: "С ДМЗ", seg_all: "С островами",
  hint: "Перетаскивайте карту. Колесо, два пальца или двойной щелчок меняют масштаб. Нажмите на точку, чтобы увидеть название магазина, или на пустое место, чтобы найти ближайший.",
  ans_all: "все магазины", ans_only: "только {b}", dist_sub: "расстояние по прямой до ближайшего магазина",
  note_vertex: "Точка, равноудалённая от трёх магазинов", note_coast: "Точка на береговой линии", note_dmz: "На военной демаркационной линии, внутри ДМЗ",
  dokdo: " · Токто: {d} km",
  kind_vertex: "Ответ — центр описанной окружности, где сходятся три круга.", kind_coast: "Здесь ответ лежит на границе, а не в центре окружности на суше.",
  rstar: "Ответ для этой области: {r}. {kind}", half: "Радиус {h} покрывает половину территории, 10 km — {c}.",
  live_pairs: "При этом радиусе: пересекающихся пар {pairs2} · точек пересечения {pts2}", live_tri: "Треугольников Делоне по этим магазинам: {nv2}, столько же кандидатов в центры",
  nation: "Вся страна", more: "ещё {n}", here1: "Магазин в этой точке", hereN: "Магазинов в этой точке: {n}", near: "Ближайший отсюда: {b}", straight: "по прямой",
  h2_math: "Математика",
  eq1_h: "Расстояние между двумя точками", eq1_p: "Земля считается шаром радиусом 6371 км, расстояния берутся по дуге большого круга. На практике каждая точка становится единичным вектором, а длина хорды c между двумя точками переводится обратно в расстояние.",
  eq2_h: "Когда и где пересекаются два круга", eq2_p: "Два круга радиуса r пересекаются, когда расстояние ℓ между центрами не больше 2r. Точки пересечения лежат на серединном перпендикуляре и скользят по нему наружу по мере роста r.",
  eq3_h: "Где круги соприкасаются = рёбра Вороного", eq3_p: "Жёлтые линии на карте — места, где два круга продолжают соприкасаться после первой встречи. Каждая точка такой линии равноудалена от двух магазинов, поэтому линии делят территорию на области, ближайшие к каждому магазину.",
  eq4_h: "Три круга в одной точке = центр описанной окружности", eq4_p: "Точка, где три круга встречаются одновременно, — вершина диаграммы Вороного, центр окружности, описанной около треугольника из трёх магазинов. На сфере нормаль к плоскости через три единичных вектора указывает на этот центр.",
  eq5_h: "Покрытие", eq5_p: "Доля территории L, попавшая хотя бы в один круг.",
  eq6_h: "Самая дальняя точка", eq6_p: "Для каждой точки измеряется расстояние до ближайшего магазина и выбирается точка, где оно наибольшее. Пока круги растут, это последняя непокрытая точка, а радиус в этот момент и есть ответ. Кандидатов всего два вида: центры описанных окружностей на суше и точки на побережье.",
  h2_make: "Как это сделано",
  mk1: "Из общенационального файла коммерческих объектов Small Enterprise and Market Service за июнь 2026 года взяты 54 446 точек с категорией «магазин у дома». После объединения одинаковых координат остаётся 49 244 точки.",
  mk2: "Границы провинций Statistics Korea 2013 года объединены в один полигон суши с 2021 островом. Для материка без ДМЗ отрезано всё севернее южной границы ДМЗ из Natural Earth.",
  mk3: "Координаты магазинов переведены в векторы на единичной сфере, и построена их выпуклая оболочка. Каждая треугольная грань — сферический треугольник Делоне, а её нормаль — центр описанной окружности. Это занимает 0,3 секунды.",
  mk4: "Около 90 тысяч центров на суше и более 300 тысяч точек вдоль побережья с шагом 20 м проверены по KD-дереву на расстояние до ближайшего магазина, выбрано наибольшее.",
  mk5: "Для покрытия территория разбита на 1,35 млн ячеек размером около 550 м; для каждой найдено расстояние, и они сложены с весом по площади.",
  lim_h: "Ограничения",
  lim1: "Категории бизнеса взяты из исходных данных как есть. Попадают и некоторые другие точки, отнесённые к магазинам у дома, а незарегистрированные отсутствуют. На острове Хыксандо нет точек этой категории, поэтому ближайший магазин для Кагодо — на Чиндо.",
  lim2: "Границы — 2013 года, поэтому намытые позже земли не учтены.",
  lim3: "Все расстояния — по прямой. Пешком через горы гораздо дальше.",
  foot: "Магазины: Small Enterprise and Market Service, июнь 2026 · Границы: Statistics Korea 2013 · ДМЗ: Natural Earth · Подложка: Esri World Dark Gray · Идея: McFarthest point от everything.in.math · Хобби-проект, сделанный с Claude",
},
ja: {
  title: "コンビニから一番遠い場所",
  h1: 'コンビニから<span class="far">一番遠い</span>場所',
  lede: "韓国には54,446軒のコンビニがあります。どこまで離れられるでしょうか",
  lang: "言語",
  a_stage: "円が広がる地図", a_map: "すべての店舗に同じ半径の円を描いた地図", a_brands: "ブランド",
  a_slider: "半径", a_region: "範囲", a_zoom: "最遠点の拡大", a_chart: "半径ごとのカバー率", close: "閉じる",
  recenter: "自動視点", credit: "背景地図 © Esri · 地名 韓国統計庁",
  b_all: "すべて", b_gs: "GS25", b_cu: "CU", b_se: "セブン-イレブン", b_e24: "emart24",
  stores: "店舗", store_word: "店",
  cover: "国土の{cov}で、この距離以内にコンビニがあります", pairs: "重なった円 {pairs}組",
  play: "再生", pause: "停止",
  seg_south: "DMZ外の本土", seg_mainland: "DMZを含む", seg_all: "島を含む",
  hint: "ドラッグで移動、ホイール・2本指・ダブルクリックで拡大。点を押すと店名、何もない場所を押すと一番近い店が出ます",
  ans_all: "すべての店舗", ans_only: "{b}のみ", dist_sub: "一番近い店までの直線距離",
  note_vertex: "3つの店からちょうど同じ距離の一点", note_coast: "海岸線上の一点", note_dmz: "軍事境界線上、非武装地帯の中",
  dokdo: " · 独島は{d} km",
  kind_vertex: "答えは3つの円が1点で出会う外心です。", kind_coast: "ここでは答えが陸地内の外心ではなく境界線上にあります。",
  rstar: "この範囲の答え {r}。{kind}", half: "半径{h}で国土の半分、10 kmで{c}が覆われます。",
  live_pairs: "今の半径で重なった円 {pairs2}組・交点 {pts2}個", live_tri: "これらの店舗から作ったドロネー三角形 {nv2}個、外心の候補も同じ数",
  nation: "全国", more: "他{n}店", here1: "この場所の店", hereN: "この場所の店 {n}軒", near: "ここから一番近い{b}", straight: "直線距離",
  h2_math: "計算に使った式",
  eq1_h: "2点間の距離", eq1_p: "地球を半径6,371 kmの球とみなし、大円距離を使います。実際の計算では各点を単位ベクトルにし、2点を結ぶ弦の長さcから距離に戻します。",
  eq2_h: "2つの円が出会う条件と交点", eq2_p: "半径rの2つの円は、中心間の距離ℓが2r以下のとき出会います。交点は2つの中心の垂直二等分線上にあり、rが大きくなるとその線に沿って外へ滑っていきます。",
  eq3_h: "円と円が接する線 = ボロノイ境界", eq3_p: "地図の黄色い線は、2つの円が出会ったあと接し続ける場所です。その線上の点は2つの店から同じ距離にあり、各店に一番近い領域を分ける境界と同じです。",
  eq4_h: "3つの円が1点で出会うとき = 外心", eq4_p: "3つの円が同時に1点で出会う瞬間のその点がボロノイ頂点で、3つの店が作る三角形の外心です。球面上では、3つの単位ベクトルが作る平面の法線の向きがそのまま外心になります。",
  eq5_h: "カバー率", eq5_p: "国土Lのうち、どれかの店の円の中に入った面積の割合です。",
  eq6_h: "一番遠い場所", eq6_p: "すべての地点から一番近い店までの距離を測り、その値が最大の地点を選びます。円を広げたとき最後まで覆われずに残る1点がこの点で、そのときの半径が答えです。候補は陸地内の外心と海岸線上の点の2種類だけです。",
  h2_make: "作り方",
  mk1: "小商工人市場振興公団の商店街情報2026年6月版から、業種がコンビニの54,446店を抜き出しました。同じ座標をまとめると49,244地点です。",
  mk2: "韓国統計庁の2013年の市道境界をまとめ、島2,021個を含む国土ポリゴンを作りました。DMZ外の本土は、Natural EarthのDMZ南方限界線より北を切り取りました。",
  mk3: "店舗の座標を単位球上のベクトルにし、凸包を求めました。凸包の三角形の面1つが球面ドロネー三角形1つで、面の法線が外心です。0.3秒かかります。",
  mk4: "陸地内の外心約9万個と、海岸線を20 m間隔で取った30万以上の点を、KD木で一番近い店と照合して最大値を選びました。",
  mk5: "カバー率は国土を約550 mの格子135万マスに分け、各マスの距離を求めて面積で重み付けして積み上げました。",
  lim_h: "限界",
  lim1: "商店街情報の業種分類をそのまま使いました。コンビニに分類された他の店も含まれ、登録されていない店は抜けています。黒山島にはコンビニに分類された店がないため、可居島の最寄りは珍島になりました。",
  lim2: "境界は2013年基準のため、その後の埋立地は反映していません。",
  lim3: "距離はすべて直線の大円距離です。山道を歩けばずっと遠くなります。",
  foot: "店舗: 小商工人市場振興公団 2026年6月 · 境界: 韓国統計庁 2013 · DMZ: Natural Earth · 背景地図: Esri World Dark Gray · 着想: everything.in.math の McFarthest point · Claudeで作った趣味のプロジェクト",
},
zh: {
  title: "离便利店最远的地方",
  h1: '离便利店<span class="far">最远</span>的地方',
  lede: "韩国有54,446家便利店。离它们最远能有多远？",
  lang: "语言",
  a_stage: "圆圈不断扩大的地图", a_map: "每家店周围画上同样半径圆圈的地图", a_brands: "品牌",
  a_slider: "半径", a_region: "范围", a_zoom: "最远点放大", a_chart: "不同半径的覆盖率", close: "关闭",
  recenter: "自动视角", credit: "底图 © Esri · 地名 韩国统计厅",
  b_all: "全部", b_gs: "GS25", b_cu: "CU", b_se: "7-Eleven", b_e24: "emart24",
  stores: "门店", store_word: "便利店",
  cover: "{cov}的国土在这个距离内有便利店", pairs: "相互重叠的圆 {pairs}对",
  play: "播放", pause: "暂停",
  seg_south: "不含DMZ的本土", seg_mainland: "含DMZ", seg_all: "含岛屿",
  hint: "拖动移动地图，用滚轮、双指或双击缩放。点一下圆点显示店名，点空白处显示最近的便利店",
  ans_all: "全部门店", ans_only: "仅{b}", dist_sub: "到最近门店的直线距离",
  note_vertex: "与三家店距离完全相同的一点", note_coast: "海岸线上的一点", note_dmz: "军事分界线上，非军事区内",
  dokdo: " · 独岛 {d} km",
  kind_vertex: "答案是三个圆交于一点的外心。", kind_coast: "这里的答案在边界上，而不是陆地内的外心。",
  rstar: "该范围的答案 {r}。{kind}", half: "半径{h}可覆盖一半国土，10 km可覆盖{c}。",
  live_pairs: "当前半径下重叠的圆 {pairs2}对 · 交点 {pts2}个", live_tri: "由这些门店构成的德劳内三角形 {nv2}个，外心候选数量相同",
  nation: "全国", more: "另外{n}家", here1: "此处门店", hereN: "此处门店 {n}家", near: "离这里最近的{b}", straight: "直线距离",
  h2_math: "计算公式",
  eq1_h: "两点间距离", eq1_p: "把地球看作半径6,371 km的球体，使用大圆距离。实际计算时把每个点变成单位向量，再由两点间的弦长c换算回距离。",
  eq2_h: "两圆相交的条件与交点", eq2_p: "半径为r的两个圆在圆心距离ℓ不超过2r时相交。交点位于两个圆心的垂直平分线上，随着r变大沿这条线向外滑动。",
  eq3_h: "圆与圆相接的线 = 沃罗诺伊边界", eq3_p: "地图上的黄线是两个圆相遇后一直相接的位置。线上每一点到两家店的距离相同，因此这些线把国土划分为离各家店最近的区域。",
  eq4_h: "三个圆交于一点 = 外心", eq4_p: "三个圆同时交于一点时，那一点就是沃罗诺伊顶点，也是三家店构成的三角形的外心。在球面上，三个单位向量所在平面的法线方向就是外心。",
  eq5_h: "覆盖率", eq5_p: "国土L中至少落在一家店圆内的面积比例。",
  eq6_h: "最远的地方", eq6_p: "测量每个点到最近门店的距离，选出距离最大的点。圆圈扩大时最后一个没被覆盖的点就是它，那一刻的半径就是答案。候选只有两类：陆地内的外心和海岸线上的点。",
  h2_make: "制作方法",
  mk1: "从韩国小商工人市场振兴公团2026年6月版全国商圈数据中，提取了业态为便利店的54,446家。合并相同坐标后为49,244个点。",
  mk2: "合并韩国统计厅2013年的市道边界，做成包含2,021个岛屿的国土多边形。不含DMZ的本土则切掉了Natural Earth中DMZ南方界线以北的部分。",
  mk3: "把门店坐标变成单位球上的向量并求凸包。凸包的每个三角形面就是一个球面德劳内三角形，面的法线就是外心。耗时0.3秒。",
  mk4: "用KD树把陆地内约9万个外心和沿海岸线每隔20 m取的30多万个点与最近门店比对，选出最大值。",
  mk5: "覆盖率是把国土分成约550 m的135万个网格，求出每格的距离后按面积加权累计。",
  lim_h: "局限",
  lim1: "直接沿用数据中的业态分类。被归为便利店的其他商店也包括在内，未登记的店则没有。黑山岛没有被归为便利店的店，所以可居岛最近的店在珍岛。",
  lim2: "边界以2013年为准，之后的填海地未计入。",
  lim3: "所有距离都是直线大圆距离。走山路要远得多。",
  foot: "门店: 韩国小商工人市场振兴公团 2026年6月 · 边界: 韩国统计厅 2013 · DMZ: Natural Earth · 底图: Esri World Dark Gray · 灵感: everything.in.math 的 McFarthest point · 用Claude做的业余项目",
},
hi: {
  title: "सुविधा स्टोर से सबसे दूर की जगह",
  h1: 'सुविधा स्टोर से <span class="far">सबसे दूर</span> की जगह',
  lede: "दक्षिण कोरिया में 54,446 सुविधा स्टोर हैं। इनसे आप कितनी दूर जा सकते हैं?",
  lang: "भाषा",
  a_stage: "बढ़ते वृत्तों का नक्शा", a_map: "हर स्टोर के चारों ओर एक जैसी त्रिज्या वाला वृत्त", a_brands: "ब्रांड",
  a_slider: "त्रिज्या", a_region: "क्षेत्र", a_zoom: "सबसे दूर के बिंदु का क़रीबी दृश्य", a_chart: "त्रिज्या के अनुसार कवरेज", close: "बंद करें",
  recenter: "स्वतः दृश्य", credit: "आधार नक्शा © Esri · स्थान-नाम Statistics Korea",
  b_all: "सभी", b_gs: "GS25", b_cu: "CU", b_se: "7-Eleven", b_e24: "emart24",
  stores: "स्टोर", store_word: "स्टोर",
  cover: "{cov} भूमि पर इस दूरी के भीतर एक स्टोर है", pairs: "एक-दूसरे पर चढ़े वृत्तों के {pairs} जोड़े",
  play: "चलाएँ", pause: "रोकें",
  seg_south: "DMZ के बाहर मुख्य भूमि", seg_mainland: "DMZ सहित", seg_all: "द्वीपों सहित",
  hint: "नक्शा खींचकर हिलाएँ। व्हील, दो उँगलियों या डबल-क्लिक से ज़ूम करें। किसी बिंदु पर टैप करें तो स्टोर का नाम दिखेगा, खाली जगह पर टैप करें तो सबसे पास का स्टोर।",
  ans_all: "सभी स्टोर", ans_only: "केवल {b}", dist_sub: "सबसे पास के स्टोर तक सीधी दूरी",
  note_vertex: "तीन स्टोर से बिल्कुल बराबर दूरी पर एक बिंदु", note_coast: "तटरेखा पर एक बिंदु", note_dmz: "सैन्य सीमांकन रेखा पर, DMZ के भीतर",
  dokdo: " · डोकडो: {d} km",
  kind_vertex: "उत्तर परिकेंद्र है, जहाँ तीन वृत्त मिलते हैं।", kind_coast: "यहाँ उत्तर सीमा पर है, ज़मीन के भीतर किसी परिकेंद्र पर नहीं।",
  rstar: "इस क्षेत्र का उत्तर: {r}। {kind}", half: "{h} की त्रिज्या आधी भूमि ढक लेती है, और 10 km {c} भूमि।",
  live_pairs: "इस त्रिज्या पर: {pairs2} जोड़े एक-दूसरे पर · {pts2} प्रतिच्छेद बिंदु", live_tri: "इन स्टोर से बने {nv2} डेलोने त्रिभुज, और उतने ही परिकेंद्र उम्मीदवार",
  nation: "पूरा देश", more: "+{n} और", here1: "इस जगह का स्टोर", hereN: "इस जगह {n} स्टोर", near: "यहाँ से सबसे पास का {b}", straight: "सीधी दूरी",
  h2_math: "गणित",
  eq1_h: "दो बिंदुओं के बीच दूरी", eq1_p: "पृथ्वी को 6,371 km त्रिज्या वाला गोला मानकर महान-वृत्त दूरी ली जाती है। व्यवहार में हर बिंदु को इकाई सदिश बनाया जाता है, और दो बिंदुओं के बीच की जीवा c की लंबाई से दूरी निकाली जाती है।",
  eq2_h: "दो वृत्त कब और कहाँ मिलते हैं", eq2_p: "r त्रिज्या वाले दो वृत्त तब मिलते हैं जब उनके केंद्रों के बीच की दूरी ℓ अधिकतम 2r हो। प्रतिच्छेद बिंदु केंद्रों के लंब समद्विभाजक पर होते हैं और r बढ़ने पर उसी रेखा पर बाहर खिसकते हैं।",
  eq3_h: "जहाँ वृत्त छूते हैं = वोरोनोई किनारे", eq3_p: "नक्शे की पीली रेखाएँ वहाँ हैं जहाँ दो वृत्त पहली बार मिलने के बाद छूते रहते हैं। ऐसी रेखा का हर बिंदु दो स्टोर से बराबर दूर है, इसलिए ये रेखाएँ भूमि को हर स्टोर के सबसे पास वाले हिस्सों में बाँटती हैं।",
  eq4_h: "तीन वृत्त एक बिंदु पर = परिकेंद्र", eq4_p: "जिस बिंदु पर तीन वृत्त एक साथ मिलते हैं वह वोरोनोई शीर्ष है, यानी तीन स्टोर से बने त्रिभुज का परिकेंद्र। गोले पर, तीन इकाई सदिशों से बने तल का अभिलंब सीधे परिकेंद्र की ओर इशारा करता है।",
  eq5_h: "कवरेज", eq5_p: "भूमि L का वह हिस्सा जो कम से कम एक स्टोर के वृत्त के भीतर है।",
  eq6_h: "सबसे दूर का बिंदु", eq6_p: "हर बिंदु से सबसे पास के स्टोर तक की दूरी मापकर वह बिंदु चुना जाता है जहाँ यह सबसे ज़्यादा हो। वृत्त बढ़ते हुए यही आख़िरी बिना ढका बिंदु होता है, और उस पल की त्रिज्या ही उत्तर है। उम्मीदवार केवल दो तरह के हैं: ज़मीन पर परिकेंद्र और तटरेखा पर बिंदु।",
  h2_make: "यह कैसे बना",
  mk1: "Small Enterprise and Market Service की जून 2026 की राष्ट्रीय व्यावसायिक फ़ाइल से सुविधा स्टोर के रूप में दर्ज 54,446 दुकानें ली गईं। एक जैसे निर्देशांक मिलाने पर 49,244 बिंदु बचते हैं।",
  mk2: "Statistics Korea की 2013 की प्रांतीय सीमाओं को मिलाकर 2,021 द्वीपों वाला एक भूमि बहुभुज बनाया गया। DMZ के बाहर की मुख्य भूमि के लिए Natural Earth की DMZ दक्षिणी सीमा रेखा के उत्तर का हिस्सा काट दिया गया।",
  mk3: "स्टोर के निर्देशांकों को इकाई गोले पर सदिश बनाकर उनका उत्तल आवरण निकाला गया। आवरण का हर त्रिभुजाकार फलक एक गोलीय डेलोने त्रिभुज है, और उसका अभिलंब एक परिकेंद्र। इसमें 0.3 सेकंड लगते हैं।",
  mk4: "ज़मीन पर लगभग 90,000 परिकेंद्र और तटरेखा पर हर 20 m पर लिए गए 3 लाख से ज़्यादा बिंदुओं को KD-ट्री से उनके सबसे पास के स्टोर से मिलाकर सबसे बड़ी दूरी चुनी गई।",
  mk5: "कवरेज के लिए भूमि को लगभग 550 m के 13.5 लाख खानों में बाँटकर हर खाने की दूरी निकाली गई और क्षेत्रफल के भार से जोड़ा गया।",
  lim_h: "सीमाएँ",
  lim1: "स्रोत डेटा की व्यवसाय श्रेणियाँ जैसी हैं वैसी ली गई हैं। सुविधा स्टोर के रूप में दर्ज कुछ दूसरी दुकानें भी शामिल हैं, और बिना पंजीकरण वाले स्टोर छूट गए हैं। हेउकसानदो पर कोई सुविधा स्टोर दर्ज नहीं है, इसलिए गागेओदो का सबसे पास का स्टोर जिंदो पर है।",
  lim2: "सीमाएँ 2013 की हैं, इसलिए उसके बाद समुद्र से निकाली गई ज़मीन शामिल नहीं है।",
  lim3: "सभी दूरियाँ सीधी रेखा में हैं। पहाड़ों से पैदल जाएँ तो कहीं ज़्यादा दूर है।",
  foot: "स्टोर: Small Enterprise and Market Service, जून 2026 · सीमाएँ: Statistics Korea 2013 · DMZ: Natural Earth · आधार नक्शा: Esri World Dark Gray · प्रेरणा: everything.in.math का McFarthest point · Claude से बना एक शौक़िया प्रोजेक्트",
},
};

// ── 한글 → 로마자 ──
(() => {
  const I = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h"];
  const V = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i"];
  const F = ["", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l", "l", "p", "l", "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t", "p", "t"];
  const F2I = { 1: "g", 2: "kk", 4: "n", 7: "d", 8: "r", 16: "m", 17: "b", 19: "s", 20: "ss", 22: "j", 23: "ch", 24: "k", 25: "t", 26: "p", 27: "h" };
  const isH = ch => { const c = ch.charCodeAt(0); return c >= 0xAC00 && c <= 0xD7A3; };
  function syllables(w) {
    const s = [...w], out = [];
    let carry = null;
    for (let i = 0; i < s.length; i++) {
      const c = s[i].charCodeAt(0) - 0xAC00, L = Math.floor(c / 588), Vi = Math.floor((c % 588) / 28), T = c % 28;
      let ini = carry !== null ? carry : I[L]; carry = null;
      const nx = i + 1 < s.length ? Math.floor((s[i + 1].charCodeAt(0) - 0xAC00) / 588) : -1;
      let fin = F[T];
      if (T && nx >= 0) {
        if (nx === 11 && F2I[T]) { fin = ""; carry = F2I[T]; }                       // 받침이 다음 소리로 넘어감
        else if (nx === 5) {                                                          // 다음이 ㄹ
          if (T === 8 || T === 4) { fin = "l"; carry = "l"; }
          else if (T === 21 || T === 16) carry = "n";
          else if (fin === "k") { fin = "ng"; carry = "n"; }
          else if (fin === "p") { fin = "m"; carry = "n"; }
        } else if (nx === 2 || nx === 6) {                                            // 다음이 ㄴ ㅁ
          if (T === 8 && nx === 2) { fin = "l"; carry = "l"; }
          else if (fin === "k") fin = "ng"; else if (fin === "p") fin = "m"; else if (fin === "t") fin = "n";
        }
      }
      out.push(ini + V[Vi] + fin);
    }
    return out.join("");
  }
  const cap = t => t ? t[0].toUpperCase() + t.slice(1) : t;
  function chunks(word) {      // 한글 덩어리만 바꾸고 숫자·영문은 그대로
    return word.replace(/[가-힣]+/g, m => cap(syllables(m)));
  }
  const SIDO = {
    "서울특별시": "Seoul", "부산광역시": "Busan", "대구광역시": "Daegu", "인천광역시": "Incheon", "광주광역시": "Gwangju", "대전광역시": "Daejeon",
    "울산광역시": "Ulsan", "세종특별자치시": "Sejong", "경기도": "Gyeonggi", "강원도": "Gangwon", "강원특별자치도": "Gangwon", "충청북도": "Chungbuk",
    "충청남도": "Chungnam", "전라북도": "Jeonbuk", "전북특별자치도": "Jeonbuk", "전라남도": "Jeonnam", "경상북도": "Gyeongbuk", "경상남도": "Gyeongnam",
    "제주특별자치도": "Jeju", "전남광주통합특별시": "Jeonnam-Gwangju",
    "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon", "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong",
    "경기": "Gyeonggi", "강원": "Gangwon", "충북": "Chungbuk", "충남": "Chungnam", "전북": "Jeonbuk", "전남": "Jeonnam", "경북": "Gyeongbuk",
    "경남": "Gyeongnam", "제주": "Jeju",
  };
  const SUFFIX = ["대로", "시", "군", "구", "읍", "면", "동", "리", "가", "로", "길"];
  // 지명: 행정구역 끝글자 앞에 하이픈 (울진군 → Uljin-gun)
  window.romPlace = s => s.split(/\s+/).map(tok => {
    if (SIDO[tok]) return SIDO[tok];
    if (!/[가-힣]/.test(tok)) return tok;
    for (const sf of SUFFIX) {
      if (tok.length > sf.length && tok.endsWith(sf)) {
        const stem = tok.slice(0, -sf.length);
        if (/[가-힣0-9]$/.test(stem)) return chunks(stem) + "-" + syllables(sf);
      }
    }
    return chunks(tok);
  }).join(" ");
  // 상호: 브랜드는 원래 표기, 끝의 '점'은 뺌, 한글과 영문 사이 띄움
  const BRAND = [[/지에스\s?25|지에스이십오/g, "GS25 "], [/씨유/g, "CU "], [/세븐일레븐|코리아세븐/g, "7-Eleven "], [/이마트\s?24/g, "emart24 "], [/미니스톱/g, "Ministop "], [/비지에프리테일/g, "BGF Retail "]];
  window.romName = s => {
    let t = s;
    for (const [re, rep] of BRAND) t = t.replace(re, rep);
    t = t.replace(/([A-Za-z0-9])([가-힣])/g, "$1 $2").replace(/([가-힣])([A-Za-z])/g, "$1 $2");
    return t.split(/\s+/).filter(Boolean).map(tok => {
      if (tok !== "편의점" && tok.length > 1 && /[가-힣]점$/.test(tok)) tok = tok.slice(0, -1);
      return chunks(tok);
    }).join(" ");
  };
  window.isHangul = isH;
})();
