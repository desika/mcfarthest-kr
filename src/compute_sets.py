"""브랜드별 편의점 최원점 · 덮인 비율 · 확대 화면 거리장 → out/sets.json, out/sets_fields.js

compute.py 와 같은 방법을 전체 · GS25 · CU · 세븐일레븐 · 이마트24 다섯 묶음에 각각 적용한다.
  최원점 p* = argmax_{p∈L} min_i d(p, s_i)
  후보 = 육지 안 보로노이 꼭짓점(볼록껍질 면의 법선) ∪ 경계선 위 촘촘한 점
"""
import base64, csv, json, math, sys, time, zlib
from pathlib import Path

import numpy as np
import shapely
from scipy.spatial import ConvexHull, cKDTree
from shapely.geometry import shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brands import SETS, brand

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
R = 6371.0088
LON0, LAT1, KX = 124.55, 38.68, math.cos(math.radians(36))
KMX, KMY = 111.320 * KX, 110.95
T0 = time.time()
def log(*a): print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)

def unit(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)
def to_lonlat(v):
    v = v / np.linalg.norm(v, axis=-1, keepdims=True)
    return np.degrees(np.arctan2(v[..., 1], v[..., 0])), np.degrees(np.arcsin(v[..., 2]))
def arc(c): return 2 * R * np.arcsin(np.clip(c / 2, 0, 1))
def proj(lon, lat): return (np.asarray(lon) - LON0) * KMX, (LAT1 - np.asarray(lat)) * KMY

# ── 공통: 점포 · 육지 · 범위 ──
rows = list(csv.DictReader(open(ROOT / "data" / "stores.csv", encoding="utf-8")))
lon_all = np.array([float(r["lon"]) for r in rows]); lat_all = np.array([float(r["lat"]) for r in rows])
br_all = np.array([brand(r["name"]) for r in rows])

gj = json.load(open(ROOT / "data" / "skorea_provinces_geo.json", encoding="utf-8"))
land = shapely.union_all([shape(f["geometry"]) for f in gj["features"]])
mainland = max(land.geoms, key=lambda p: p.area)
ne = json.load(open(ROOT / "data" / "ne_bl.geojson", encoding="utf-8"))
sll = next(f for f in ne["features"] if f["properties"].get("NAME") == "Korean Demilitarized Zone" and f["properties"].get("ADM0_A3_L") == "KOR")
L = np.array(sll["geometry"]["coordinates"]); L = L if L[0, 0] < L[-1, 0] else L[::-1]
cut = shapely.Polygon([*L.tolist(), [L[-1, 0] + 0.5, L[-1, 1]], [L[-1, 0] + 0.5, 39.5], [L[0, 0], 39.5]])
south = mainland.difference(cut); south = max(getattr(south, "geoms", [south]), key=lambda g: g.area)
REG = {"south": south, "mainland": mainland, "all": land}
for g in REG.values(): shapely.prepare(g)
BND = {k: shapely.get_coordinates(shapely.segmentize(g.boundary, 0.0002)) for k, g in REG.items()}
BNDU = {k: unit(v[:, 0], v[:, 1]) for k, v in BND.items()}
log("경계점", {k: len(v) for k, v in BND.items()})

# 덮인 비율용 격자 (compute.py 와 같은 약 556 m)
PX = 0.0050
LON1, LAT0 = 131.95, 33.05
W = int((LON1 - LON0) * KX / PX); H = int((LAT1 - LAT0) / PX)
gx = LON0 + (np.arange(W) + 0.5) * PX / KX; gy = LAT1 - (np.arange(H) + 0.5) * PX
GX, GY = np.meshgrid(gx, gy)
MASK = {k: shapely.contains_xy(g, GX, GY) for k, g in REG.items()}
GU = {k: unit(GX[m], GY[m]) for k, m in MASK.items()}
AW = {k: np.cos(np.radians(GY[m])) for k, m in MASK.items()}
RS = np.round(np.concatenate([np.arange(0, 2, 0.02), np.arange(2, 10, 0.1), np.arange(10, 160.5, 0.5)]), 3)
log("격자", W, H)

# 지명 붙이기
MUNI = [(f["properties"]["name"], shape(f["geometry"])) for f in json.load(open(ROOT / "data" / "muni_simple.json", encoding="utf-8"))["features"]]
SUB = [(f["properties"]["name"], shape(f["geometry"])) for f in json.load(open(ROOT / "data" / "submuni_simple.json", encoding="utf-8"))["features"]]
PROV = [(f["properties"]["name"], shape(f["geometry"])) for f in json.load(open(ROOT / "data" / "skorea_provinces_geo_simple.json", encoding="utf-8"))["features"]]
SHORT = {"서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
         "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기", "강원도": "강원", "충청북도": "충북", "충청남도": "충남",
         "전라북도": "전북", "전라남도": "전남", "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주"}
def place(lon, lat):
    pt = shapely.Point(lon, lat)
    near = lambda lst: min(lst, key=lambda t: t[1].distance(pt))[0]
    return f"{SHORT.get(near(PROV), near(PROV))} {near(MUNI)} {near(SUB)}"

def solve(tree, V, vd, vi, vlon, vlat, k, rows_idx):
    g = REG[k]
    vin = shapely.contains_xy(g, vlon, vlat)
    bv = int(np.argmax(np.where(vin, vd[:, 0], -1)))
    c, bi = tree.query(BNDU[k], k=3); bd = arc(c)
    bb = int(np.argmax(bd[:, 0]))
    if vd[bv, 0] >= bd[bb, 0]:
        kind, plon, plat, dist, ids = "vertex", vlon[bv], vlat[bv], vd[bv], vi[bv]
    else:
        kind, plon, plat, dist, ids = "coast", BND[k][bb, 0], BND[k][bb, 1], bd[bb], bi[bb]
    in_dmz = bool(cut.contains(shapely.Point(plon, plat))) or (k != "south" and float(shapely.Point(plon, plat).distance(shapely.LineString(L))) < 0.03)
    stores = []
    for d, i in zip(dist, ids):
        r = rows[rows_idx[i]]
        stores.append({"name": r["name"], "branch": r["branch"], "addr": r["addr"], "lon": float(r["lon"]), "lat": float(r["lat"]), "d": round(float(d), 4)})
    return {"kind": kind, "lon": float(plon), "lat": float(plat), "r": round(float(dist[0]), 4), "stores": stores,
            "place": place(plon, plat), "dmz": in_dmz}

def coverage(tree, k):
    c, _ = tree.query(GU[k]); d = arc(c); w = AW[k]
    o = np.argsort(d); d, cw = d[o], np.cumsum(w[o]) / w.sum()
    idx = np.searchsorted(d, RS, side="right") - 1
    return np.where(idx >= 0, cw[np.maximum(idx, 0)], 0.0).round(5).tolist()

def pack(dist10, flags):
    delta = np.diff(dist10.astype(np.int32), axis=1, prepend=0).astype(np.int16)
    return base64.b64encode(zlib.compress(delta.astype("<i2").tobytes() + flags.astype(np.uint8).tobytes(), 9)).decode()

ZW, ZH = 640, 512
def zoom_field(tree, res):
    cx, cy = proj(res["lon"], res["lat"]); hk = 3.1 * res["r"]; wk = hk * ZW / ZH
    dx, dy = wk / ZW, hk / ZH; x0, y0 = float(cx) - wk / 2, float(cy) - hk / 2
    Xg = x0 + (np.arange(ZW) + 0.5) * dx; Yg = y0 + (np.arange(ZH) + 0.5) * dy
    ZX, ZY = np.meshgrid(Xg, Yg); glon, glat = LON0 + ZX / KMX, LAT1 - ZY / KMY
    c, nid = tree.query(unit(glon.ravel(), glat.ravel()))
    D = arc(c).reshape(ZH, ZW); NID = nid.reshape(ZH, ZW)
    inl = shapely.contains_xy(land, glon, glat)
    edge = np.zeros((ZH, ZW), bool); edge[:, 1:] |= NID[:, 1:] != NID[:, :-1]; edge[1:, :] |= NID[1:, :] != NID[:-1, :]
    return {"w": ZW, "h": ZH, "x0": x0, "y0": y0, "dx": dx, "dy": dy,
            "b64": pack(np.minimum(np.round(D * 100), 65535).astype(np.uint16), (inl * 1 | edge * 2).astype(np.uint8))}

out, fields = {}, {}
for key, label in SETS:
    sel = np.ones(len(rows), bool) if key == "all" else br_all == key
    idx = np.nonzero(sel)[0]
    k6 = np.round(lon_all[idx], 6) * 1e7 + np.round(lat_all[idx], 6)
    _, first = np.unique(k6, return_index=True); first.sort()
    rows_idx = idx[first]
    S = unit(lon_all[rows_idx], lat_all[rows_idx]); tree = cKDTree(S)
    hull = ConvexHull(S)
    A, B, Cc = (S[hull.simplices[:, j]] for j in range(3))
    Nn = np.cross(B - A, Cc - A); Nn /= np.linalg.norm(Nn, axis=1, keepdims=True); Nn *= np.sign(np.einsum("ij,ij->i", Nn, A))[:, None]
    vlon, vlat = to_lonlat(Nn)
    inbox = (vlon > 124) & (vlon < 132.5) & (vlat > 32.5) & (vlat < 39)
    V, vlon, vlat = Nn[inbox], vlon[inbox], vlat[inbox]
    c, vi = tree.query(V, k=3); vd = arc(c)
    res = {k: solve(tree, V, vd, vi, vlon, vlat, k, rows_idx) for k in REG}
    curve = {k: coverage(tree, k) for k in REG}
    # 겹친 원 쌍(중심거리 ≤ 2r): 전부 세면 반지름이 클 때 수십 분 → 점포 4천 곳 표본으로 세어 전체로 환산
    chords = 2 * np.sin(np.minimum(2 * RS, R * math.pi) / (2 * R))
    rng = np.random.default_rng(7); ns = min(len(S), 4000)
    samp = cKDTree(S[rng.choice(len(S), ns, replace=False)])
    cnt = samp.count_neighbors(tree, chords) - ns            # 표본 점마다 이웃 수 합 (자기 자신 제외)
    pairs = np.round(cnt * len(S) / ns / 2).astype(np.int64).tolist()
    half = {k: round(float(np.interp(0.5, curve[k], RS)), 3) for k in REG}
    out[key] = {"label": label, "n": int(sel.sum()), "nUnique": int(len(rows_idx)), "nTri": int(len(hull.simplices)),
                "results": res, "cov": curve, "pairs": pairs, "half": half}
    for k in REG: fields[f"{key}_{k}"] = zoom_field(tree, res[k])
    log(label, sel.sum(), "점포 ·", {k: (res[k]["place"], res[k]["r"]) for k in REG})

json.dump({"r": RS.tolist(), "sets": out}, open(ROOT / "out" / "sets.json", "w", encoding="utf-8"), ensure_ascii=False)
js = "window.KF=Object.assign(window.KF||{}," + json.dumps(fields, separators=(",", ":")) + ");"
(ROOT / "out" / "sets_fields.js").write_text(js, encoding="utf-8")
log("sets_fields.js", len(js) // 1024, "KB")
