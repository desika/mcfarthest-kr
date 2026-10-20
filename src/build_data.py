"""화면용 데이터 묶기 → out/page_data.js

입력: data/stores.csv · out/result.json(전국 거리장 정보) · out/sets.json(브랜드별 결과, compute_sets.py)

점포 좌표는 화면 좌표계 km 로 바꿔 10 m 단위 uint16 두 개씩 → base64.
화면 좌표계: X = (lon − LON0)·111.320·cos36°, Y = (LAT1 − lat)·110.95  (km, 등거리 원통)
"""
import base64, csv, json, math, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brands import SETS, brand
import os
DATASET = os.environ.get("MF_DATASET", "cvs")          # cvs = 편의점(기본), tobacco = 담배소매점
STORES_CSV = "tobacco_stores.csv" if DATASET == "tobacco" else "stores.csv"
SUF = "" if DATASET == "cvs" else "_" + DATASET
if DATASET == "tobacco": SETS = [("all", "Tobacco")]

import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import shape

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
LON0, LAT1, KX = 124.55, 38.68, math.cos(math.radians(36))
KMX, KMY = 111.320 * KX, 110.95

def proj(lon, lat):
    return (np.asarray(lon) - LON0) * KMX, (LAT1 - np.asarray(lat)) * KMY

res = json.load(open(ROOT / "out" / "result.json", encoding="utf-8"))
rows = list(csv.DictReader(open(ROOT / "data" / STORES_CSV, encoding="utf-8")))
lon = np.array([float(r["lon"]) for r in rows]); lat = np.array([float(r["lat"]) for r in rows])
key = np.round(lon, 6) * 1e7 + np.round(lat, 6)
_, first = np.unique(key, return_index=True); first.sort()
x, y = proj(lon[first], lat[first])
q = np.stack([np.round(x * 100), np.round(y * 100)], 1)
assert q.min() >= 0 and q.max() < 65536, (q.min(), q.max())
stores_b64 = base64.b64encode(q.astype("<u2").tobytes()).decode()

# 브랜드 코드: 0 그 밖 · 1 GS25 · 2 CU · 3 세븐일레븐 · 4 이마트24
CODE = {"etc": 0, "gs": 1, "cu": 2, "se": 3, "e24": 4}
br_all = np.array([CODE[brand(r["name"])] for r in rows], np.uint8)
# 같은 좌표 점포들: 점마다 들어 있는 브랜드 비트, 점 색깔은 첫 점포 브랜드
_, first_u, inv = np.unique(key, return_index=True, return_inverse=True)
uidx = np.argsort(np.argsort(first_u))[inv]        # 화면 점 번호(= 첫 등장 순서)로 맞춤
assert (uidx[first] == np.arange(len(first))).all()
mask = np.zeros(len(first), np.uint8)
np.bitwise_or.at(mask, uidx, (1 << br_all).astype(np.uint8))
brands_b64 = base64.b64encode(br_all[first].tobytes()).decode()
mask_b64 = base64.b64encode(mask.tobytes()).decode()
brand_count = {k: int((br_all == v).sum()) for k, v in CODE.items()}

# 점포 이름 · 동네: 클릭했을 때 보여 줌
dongs = sorted({f'{r["sigungu"]} {r["dong"]}' for r in rows}); dong_i = {d: i for i, d in enumerate(dongs)}
names = [(r["name"] + (" " + r["branch"] if r["branch"] else "")).strip() for r in rows]
store_u = base64.b64encode(uidx.astype("<u2").tobytes()).decode()
store_b = base64.b64encode(br_all.tobytes()).decode()
store_d = base64.b64encode(np.array([dong_i[f'{r["sigungu"]} {r["dong"]}'] for r in rows], "<u2").tobytes()).decode()

# 육지: 정밀 시도 경계를 합쳐 세 단계로 단순화 → 링 목록 (0.01 km 반올림)
#   0: 0.008° 전국용 · 1: 0.003° 중간 · 2: 0.0015°(약 150 m) 확대용
gj = json.load(open(ROOT / "data" / "skorea_provinces_geo.json", encoding="utf-8"))
land_full = shapely.union_all([shape(f["geometry"]) for f in gj["features"]])
def rings_of(geom, min_area=0.0):
    out = []
    for p in getattr(geom, "geoms", [geom]):
        if p.area < min_area: continue
        for ring in [p.exterior, *p.interiors]:
            c = np.asarray(ring.coords)
            if len(c) < 4: continue
            px, py = proj(c[:, 0], c[:, 1])
            out.append(np.round(np.stack([px, py], 1), 2).ravel().tolist())
    return out
land_lod = [rings_of(land_full.simplify(0.008), 2e-6), rings_of(land_full.simplify(0.003), 5e-7), rings_of(land_full.simplify(0.0015))]
rings = land_lod[2]
print("링", [len(r) for r in land_lod], "좌표", [sum(len(x) for x in r) // 2 for r in land_lod])

def P(lo, la):
    a, b = proj(lo, la); return [round(float(a), 3), round(float(b), 3)]

# 독도 · 울릉도 참고 거리
def unit(lo, la):
    lo, la = np.radians(lo), np.radians(la)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
tree = cKDTree(unit(lon[first], lat[first]))
def dist_km(lo, la):
    c, _ = tree.query(unit(np.array([lo]), np.array([la])))
    return round(float(2 * 6371.0088 * np.arcsin(c[0] / 2)), 2)


# 지명: 시도 · 시군구 · 읍면동 이름과 라벨 위치 (가장 큰 조각의 극점 = polylabel)
from shapely.ops import polylabel
SHORT = {"서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천", "광주광역시": "광주",
         "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기", "강원도": "강원",
         "충청북도": "충북", "충청남도": "충남", "전라북도": "전북", "전라남도": "전남", "경상북도": "경북",
         "경상남도": "경남", "제주특별자치도": "제주"}
def label_points(fn, short=None):
    g = json.load(open(ROOT / "data" / fn, encoding="utf-8")); out = []
    for f in g["features"]:
        geom = shape(f["geometry"]).buffer(0)
        part = max(getattr(geom, "geoms", [geom]), key=lambda q: q.area)
        try: pt = polylabel(part, tolerance=0.002)
        except Exception: pt = part.representative_point()
        name = f["properties"]["name"]; name = short.get(name, name) if short else name
        out.append([name, *P(pt.x, pt.y), round(part.area * 1e4, 1)])
    return out
labels = {"sido": label_points("skorea_provinces_geo_simple.json", SHORT),
          "sgg": label_points("muni_simple.json"), "emd": label_points("submuni_simple.json")}

# 브랜드별 결과
SJ = json.load(open(ROOT / "out" / f"sets{SUF}.json", encoding="utf-8"))
OVERRIDE = {("all", "all"): "전남 신안군 흑산면 가거도"}
def note(rr):
    if rr["dmz"]: return "군사분계선 위, 비무장지대 안"
    return "세 편의점에서 똑같이 떨어진 한 점" if rr["kind"] == "vertex" else "해안선 위 한 점"
sets = {}
for skey, label in SETS:
    sv = SJ["sets"][skey]
    sets[skey] = {"label": label, "n": sv["n"], "nUnique": sv["nUnique"], "nTri": sv["nTri"], "half": sv["half"],
                  "cov": sv["cov"], "pairs": sv["pairs"],
                  "results": {k: {**rr, "place": OVERRIDE.get((skey, k), rr["place"]), "note": note(rr), "xy": P(rr["lon"], rr["lat"]),
                                  "stores": [{**s, "xy": P(s["lon"], s["lat"])} for s in rr["stores"]]}
                              for k, rr in sv["results"].items()}}

out = {
    "nStores": len(rows), "nUnique": int(len(first)),
    "kx": KX, "kmx": KMX, "kmy": KMY, "lon0": LON0, "lat1": LAT1,
    "curveR": SJ["r"], "sets": sets,
    "dokdo": dist_km(131.8669, 37.2414),
    "sll": [P(a, b) for a, b in res["sll"]],
    "seoul": P(126.9780, 37.5665),
    "land": rings, "landLod": land_lod[:2],
    "labels": labels,
    "stores": stores_b64, "brands": brands_b64, "brandMask": mask_b64, "brandCount": brand_count,
    "names": names, "dongs": dongs, "storeU": store_u, "storeD": store_d, "storeB": store_b,
}
js = "window.KR=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";"
(ROOT / "out" / f"page_data{SUF}.js").write_text(js, encoding="utf-8")
print("독도→가장 가까운 편의점", out["dokdo"], "km · page_data", len(js) // 1024, "KB")
