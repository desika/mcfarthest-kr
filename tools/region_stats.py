"""시도별 편의점 밀도 → out/region_stats.json

국토를 위도 0.002°(약 222 m) 격자로 나눠 칸마다 가장 가까운 편의점까지 대원거리를 구하고,
시도(통계청 2013 경계)별로 몇 km 안에 편의점이 있는 땅의 비율 · 거리 중앙값 · 가장 먼 곳을 낸다.
점포 수는 좌표가 그 시도 경계 안에 있는 점포를 센다 (상가정보의 시도명은 2026년 행정구역이라 경계와 맞추려고).
"""
import csv, json, math, sys
from pathlib import Path

import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import shape

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
R = 6371.0088
def unit(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)

rows = list(csv.DictReader(open(ROOT / "data" / "stores.csv", encoding="utf-8")))
slon = np.array([float(r["lon"]) for r in rows]); slat = np.array([float(r["lat"]) for r in rows])
tree = cKDTree(unit(slon, slat))

EN = {"서울특별시": "Seoul", "부산광역시": "Busan", "대구광역시": "Daegu", "인천광역시": "Incheon", "광주광역시": "Gwangju",
      "대전광역시": "Daejeon", "울산광역시": "Ulsan", "세종특별자치시": "Sejong", "경기도": "Gyeonggi", "강원도": "Gangwon",
      "충청북도": "Chungbuk", "충청남도": "Chungnam", "전라북도": "Jeonbuk", "전라남도": "Jeonnam", "경상북도": "Gyeongbuk",
      "경상남도": "Gyeongnam", "제주특별자치도": "Jeju"}
gj = json.load(open(ROOT / "data" / "skorea_provinces_geo.json", encoding="utf-8"))
prov = [(f["properties"]["name"], shape(f["geometry"])) for f in gj["features"]]
for _, g in prov: shapely.prepare(g)

STEP = 0.002
out = []
for name, g in prov:
    x0, y0, x1, y1 = g.bounds
    lats = np.arange(y0 + STEP / 2, y1, STEP)
    kx = STEP / math.cos(math.radians((y0 + y1) / 2))          # 칸이 대략 정사각형이 되게
    lons = np.arange(x0 + kx / 2, x1, kx)
    GX, GY = np.meshgrid(lons, lats)
    m = shapely.contains_xy(g, GX, GY)
    px, py = GX[m], GY[m]
    c, _ = tree.query(unit(px, py)); d = 2 * R * np.arcsin(np.clip(c / 2, 0, 1))
    w = np.cos(np.radians(py)); w = w / w.sum()
    area = float(m.sum() * (STEP * 110.95) * (kx * 111.32 * np.cos(np.radians(py))).mean())
    n_st = int(shapely.contains_xy(g, slon, slat).sum())
    o = np.argsort(d); cw = np.cumsum(w[o]); med = float(d[o][np.searchsorted(cw, 0.5)])
    i = int(np.argmax(d))
    out.append({"name": name, "en": EN[name], "area_km2": round(area), "stores": n_st, "per_km2": round(n_st / area, 3),
                **{f"within_{k}": round(float(w[d <= k].sum()) * 100, 1) for k in (0.5, 1, 2, 5)},
                "median_km": round(med, 2), "max_km": round(float(d[i]), 2), "max_at": [round(float(px[i]), 4), round(float(py[i]), 4)]})
    print(f"{name:8s} {area:8.0f}km² {n_st:6d} {n_st/area:6.2f}/km² ≤0.5:{out[-1]['within_0.5']:5.1f} ≤1:{out[-1]['within_1']:5.1f} ≤2:{out[-1]['within_2']:5.1f} ≤5:{out[-1]['within_5']:5.1f} 중앙 {med:5.2f} 최대 {d[i]:6.2f}", flush=True)

json.dump(out, open(ROOT / "out" / "region_stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
