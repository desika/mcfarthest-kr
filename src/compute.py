"""대한민국 편의점 최원점 계산 · 2026-10-18

입력  data/stores.csv (상가정보 편의점 54,446) · data/skorea_provinces_geo.json (통계청 2013 시도 경계)
출력  out/result.json (최원점·세 점포·곡선) · out/field.bin (거리장 래스터, deflate)

거리는 모두 구면 대원거리. 점포를 단위벡터로 바꿔 KD트리에 넣으면
현의 길이 c 로부터 d = 2R·asin(c/2) 로 정확한 대원거리가 나온다.

최원점 p* = argmax_{p∈L} min_i d(p, s_i)  — 최대 빈 원의 중심.
후보는 두 종류뿐이다.
  1) 육지 안의 보로노이 꼭짓점 = 세 점포의 외심 (세 원이 한 점에서 만남)
  2) 해안선 위의 점 (원이 바다 쪽으로 빠져나가는 경우)
"""
import csv, json, math, zlib
from pathlib import Path

import numpy as np
import shapely
from scipy.spatial import ConvexHull, cKDTree
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
R = 6371.0088  # km, 평균 지구 반지름

def unit(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)

def to_lonlat(v):
    v = v / np.linalg.norm(v, axis=-1, keepdims=True)
    return np.degrees(np.arctan2(v[..., 1], v[..., 0])), np.degrees(np.arcsin(v[..., 2]))

def arc(c):  # 현 길이 → 대원거리 km
    return 2 * R * np.arcsin(np.clip(c / 2, 0, 1))

# ── 데이터 ───────────────────────────────────────────
rows = list(csv.DictReader(open(ROOT / "data" / "stores.csv", encoding="utf-8")))
lon = np.array([float(r["lon"]) for r in rows]); lat = np.array([float(r["lat"]) for r in rows])
# 같은 좌표 중복 제거 (보로노이는 서로 다른 점이 필요)
key = np.round(lon, 6) * 1e7 + np.round(lat, 6)
_, first = np.unique(key, return_index=True); first.sort()
S = unit(lon[first], lat[first]); idx_map = first
tree = cKDTree(S)
print("점포", len(rows), "고유 좌표", len(first))

gj = json.load(open(ROOT / "data" / "skorea_provinces_geo.json", encoding="utf-8"))
land = shapely.union_all([shape(f["geometry"]) for f in gj["features"]])
polys = sorted(land.geoms, key=lambda p: -p.area)
mainland = polys[0]
# DMZ 남방한계선 (Natural Earth 10m, KOR-KOR overlay limit) 북쪽을 잘라낸 본토
ne = json.load(open(ROOT / "data" / "ne_bl.geojson", encoding="utf-8"))
sll = next(f for f in ne["features"] if f["properties"].get("NAME") == "Korean Demilitarized Zone"
           and f["properties"].get("ADM0_A3_L") == "KOR")
L = np.array(sll["geometry"]["coordinates"])
if L[0, 0] > L[-1, 0]: L = L[::-1]
cut = shapely.Polygon([*L.tolist(), [L[-1, 0] + 0.5, L[-1, 1]], [L[-1, 0] + 0.5, 39.5], [L[0, 0], 39.5]])
south = mainland.difference(cut)
south = max(getattr(south, "geoms", [south]), key=lambda g: g.area)
print("남방한계선", L[0].round(3), L[-1].round(3), "본토 면적비", round(south.area / mainland.area, 4))
shapely.prepare(land); shapely.prepare(mainland); shapely.prepare(south)

def nearest(P):
    c, i = tree.query(P, k=3)
    return arc(c), i

# ── 1) 보로노이 꼭짓점 ───────────────────────────────
# 단위구 위 점들의 볼록껍질 면 = 구면 들로네 삼각형. 면의 바깥 법선 = 세 점의 구면 외심 = 보로노이 꼭짓점
hull = ConvexHull(S)
A, Bv, C = (S[hull.simplices[:, k]] for k in range(3))
N = np.cross(Bv - A, C - A); N /= np.linalg.norm(N, axis=1, keepdims=True)
N *= np.sign(np.einsum("ij,ij->i", N, A))[:, None]
V = N
n_vertices = len(V)
vlon, vlat = to_lonlat(V)
inbox = (vlon > 124) & (vlon < 132.5) & (vlat > 32.5) & (vlat < 39)
V, vlon, vlat = V[inbox], vlon[inbox], vlat[inbox]
vd, vi = nearest(V)

# ── 2) 해안선 위 촘촘한 점 (약 20 m 간격) ──────────────
def boundary_samples(geom, step_deg=0.0002):
    # 선분을 step 이하로 잘게 쪼갠 꼭짓점 = 경계 위 촘촘한 점 (한 번 훑기)
    return shapely.get_coordinates(shapely.segmentize(geom.boundary, step_deg))

def solve(region, name):
    vin = shapely.contains_xy(region, vlon, vlat)
    bv = np.argmax(np.where(vin, vd[:, 0], -1))
    B = boundary_samples(region)
    bd, bi = nearest(unit(B[:, 0], B[:, 1]))
    bb = np.argmax(bd[:, 0])
    if vd[bv, 0] >= bd[bb, 0]:
        kind, plon, plat, dist, ids = "vertex", vlon[bv], vlat[bv], vd[bv], vi[bv]
    else:
        kind, plon, plat, dist, ids = "coast", B[bb, 0], B[bb, 1], bd[bb], bi[bb]
    print(f"[{name}] {kind} ({plat:.5f}, {plon:.5f}) r = {dist[0]:.3f} km  · 후보 꼭짓점 {vin.sum()} · 해안점 {len(B)}")
    stores = []
    for d, i in zip(dist, ids):
        r = rows[idx_map[i]]
        stores.append({"name": r["name"], "branch": r["branch"], "addr": r["addr"], "sido": r["sido"],
                       "sigungu": r["sigungu"], "lon": float(r["lon"]), "lat": float(r["lat"]), "d": round(float(d), 4)})
    return {"kind": kind, "lon": float(plon), "lat": float(plat), "r": round(float(dist[0]), 4), "stores": stores}

res_south = solve(south, "DMZ 밖 본토")
res_main = solve(mainland, "본토")
res_all = solve(land, "전체")

# ── 거리장 래스터 · 화면용 ───────────────────────────
LON0, LON1, LAT0, LAT1 = 124.55, 131.95, 33.05, 38.68
KX = math.cos(math.radians(36))           # 등거리 원통도법 가로 축척
PX = 0.0050                                # 위도 0.005° ≈ 556 m / px
W = int((LON1 - LON0) * KX / PX); H = int((LAT1 - LAT0) / PX)
gx = LON0 + (np.arange(W) + 0.5) * PX / KX
gy = LAT1 - (np.arange(H) + 0.5) * PX
GX, GY = np.meshgrid(gx, gy)
inland = shapely.contains_xy(land, GX, GY)
c, nid = tree.query(unit(GX.ravel(), GY.ravel()), k=1)
D = arc(c).reshape(H, W); NID = nid.reshape(H, W)
# 보로노이 경계 = 이웃 픽셀의 가장 가까운 점포가 다름
edge = np.zeros((H, W), bool)
edge[:, 1:] |= NID[:, 1:] != NID[:, :-1]; edge[1:, :] |= NID[1:, :] != NID[:-1, :]
# 점포 위치 픽셀
sx = ((lon[first] - LON0) * KX / PX).astype(int); sy = ((LAT1 - lat[first]) / PX).astype(int)
ok = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
dot = np.zeros((H, W), bool); dot[sy[ok], sx[ok]] = True

dist10 = np.minimum(np.round(D * 100), 65535).astype("<u2")   # 10 m 단위
flags = (inland * 1 | edge * 2 | dot * 4).astype(np.uint8)
blob = zlib.compress(dist10.tobytes() + flags.tobytes(), 9)
(OUT / "field.bin").write_bytes(blob)
print("래스터", W, H, "압축", len(blob) // 1024, "KB")

# ── 곡선: 덮인 비율 · 교차하는 원 쌍 ─────────────────
area_w = np.cos(np.radians(GY))
def coverage(region_mask, rs):
    w = area_w[region_mask]; d = D[region_mask]; o = np.argsort(d); d, cw = d[o], np.cumsum(w[o]) / w.sum()
    return [round(float(cw[np.searchsorted(d, r, side="right") - 1]) if r >= d[0] else 0.0, 5) for r in rs]

main_mask = shapely.contains_xy(mainland, GX, GY)
south_mask = shapely.contains_xy(south, GX, GY)
rs = np.round(np.concatenate([np.arange(0, 2, 0.02), np.arange(2, 10, 0.1), np.arange(10, 120.5, 0.5)]), 3)
cov_all = coverage(inland, rs); cov_main = coverage(main_mask, rs); cov_south = coverage(south_mask, rs)
# 두 원(반지름 r)이 교차 ⇔ 중심거리 ≤ 2r. 현 길이로 바꿔 쌍 개수를 센다
chords = 2 * np.sin(np.minimum(2 * rs, 2 * R * math.pi / 2) / (2 * R))
pairs = tree.count_neighbors(tree, chords)
pairs = ((pairs - len(S)) // 2).tolist()   # 자기 자신 제외, 순서쌍 → 쌍

# 육지 면적 km² (화면 래스터 기준)
# 픽셀 면적 = (경도폭 km)·(위도폭 km), 경도폭은 cos(위도) 보정 → area_w
area_all = float((area_w[inland]).sum() * (PX / KX * 111.195) * (PX * 111.195))
area_south = float((area_w[south_mask]).sum() * (PX / KX * 111.195) * (PX * 111.195))
area_main = float((area_w[main_mask]).sum() * (PX / KX * 111.195) * (PX * 111.195))

result = {
    "generated": "2026-10-18", "source": "소상공인시장진흥공단 상가정보 2026-06 · 통계청 시도 경계 2013",
    "n_stores": len(rows), "n_unique": int(len(first)), "n_vertices": int(n_vertices),
    "raster": {"w": W, "h": H, "lon0": LON0, "lat1": LAT1, "px": PX, "kx": KX},
    "south": res_south, "mainland": res_main, "all": res_all,
    "sll": L.round(4).tolist(),
    "area_km2": {"all": round(area_all), "main": round(area_main), "south": round(area_south)},
    "curve": {"r": rs.tolist(), "cov_all": cov_all, "cov_main": cov_main, "cov_south": cov_south, "pairs": pairs},
    "half": {k: round(float(np.interp(0.5, c, rs)), 3) for k, c in (("all", cov_all), ("main", cov_main), ("south", cov_south))},
}
json.dump(result, open(OUT / "result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: result[k] for k in ("area_km2", "half")}, ensure_ascii=False))
for r in (0.5, 1, 2, 5, 10):
    j = int(np.searchsorted(rs, r)); print(f"r={r}km 덮임 본토 {cov_main[j]:.3f} 전체 {cov_all[j]:.3f} 교차쌍 {pairs[j]}")
