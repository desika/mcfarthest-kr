"""거리장 래스터 묶기 → out/fields.js

  nat   : compute.py 가 만든 전국 거리장 (약 556 m/px) 재포장
  zoom_*: 각 범위 최원점 주변 확대 화면용 거리장 640×512

픽셀마다 [가장 가까운 편의점까지 거리 10 m 단위 uint16] + [플래그 1=육지 2=보로노이 경계].
거리는 행마다 앞 픽셀과의 차이로 바꿔 압축률을 높이고(브라우저에서 누적합), zlib 압축 → base64.
"""
import base64, csv, json, math, sys, zlib
from pathlib import Path

import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import shape

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
R = 6371.0088
LON0, LAT1, KX = 124.55, 38.68, math.cos(math.radians(36))
KMX, KMY = 111.320 * KX, 110.95

def unit(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)

def pack(dist10, flags):
    d = dist10.astype(np.int32)
    delta = np.diff(d, axis=1, prepend=0).astype(np.int16)        # 행 첫 칸은 원값
    blob = zlib.compress(delta.astype("<i2").tobytes() + flags.astype(np.uint8).tobytes(), 9)
    return base64.b64encode(blob).decode()

res = json.load(open(ROOT / "out" / "result.json", encoding="utf-8"))
rs = res["raster"]; W, H, PX = rs["w"], rs["h"], rs["px"]
raw = zlib.decompress((ROOT / "out" / "field.bin").read_bytes())
dist10 = np.frombuffer(raw[: W * H * 2], "<u2").reshape(H, W)
flags = np.frombuffer(raw[W * H * 2:], np.uint8).reshape(H, W) & 3
out = {"nat": {"w": W, "h": H, "x0": 0.0, "y0": 0.0, "dx": PX * 111.320, "dy": PX * 110.95, "b64": pack(dist10, flags)}}
print("전국", W, H, len(out["nat"]["b64"]) // 1024, "KB")

rows = list(csv.DictReader(open(ROOT / "data" / "stores.csv", encoding="utf-8")))
lon = np.array([float(r["lon"]) for r in rows]); lat = np.array([float(r["lat"]) for r in rows])
key = np.round(lon, 6) * 1e7 + np.round(lat, 6)
_, first = np.unique(key, return_index=True); first.sort()
tree = cKDTree(unit(lon[first], lat[first]))
gj = json.load(open(ROOT / "data" / "skorea_provinces_geo.json", encoding="utf-8"))
land = shapely.union_all([shape(f["geometry"]) for f in gj["features"]]); shapely.prepare(land)

# 확대 화면용 거리장은 compute_sets.py 가 브랜드별로 만든다

js = "window.KF=Object.assign(window.KF||{}," + json.dumps(out, separators=(",", ":")) + ");"
(ROOT / "out" / "fields.js").write_text(js, encoding="utf-8")
print("fields.js", len(js) // 1024, "KB")
