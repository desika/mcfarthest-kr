"""담배소매업 인허가로 편의점이 얼마나 잡히나 → out/tobacco_coverage.json

1) 행정안전부 담배소매업 조회서비스(info)에서 브랜드 이름이 들어간 '영업/정상' 사업장을 모두 받는다 → data/tobacco/
2) 좌표(중부원점 TM)를 경위도로 바꾸고, 상가정보 편의점과 브랜드별로 100 m 안에서 짝을 짓는다
3) 상가정보 편의점 가운데 담배소매점과 짝이 지어진 비율 = 담배소매업으로 잡히는 비율
"""
import csv, json, math, sys, time, urllib.parse, urllib.request
from pathlib import Path

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from brands import brand

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
KEY = next(l.split("=", 1)[1].strip() for l in open(ROOT / ".env", encoding="utf-8") if l.startswith("DATA_GO_KR_KEY="))
URL = "https://apis.data.go.kr/1741000/tobacco_retailers/info"
RAW = ROOT / "data" / "tobacco"; RAW.mkdir(parents=True, exist_ok=True)
QUERIES = ["GS25", "지에스25", "CU", "씨유", "세븐일레븐", "7-ELEVEN", "코리아세븐", "이마트24", "이마트 24", "emart24"]

def call(params, tries=4):
    q = {"serviceKey": KEY, "returnType": "json", **params}
    for t in range(tries):
        try:
            with urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=60) as r:
                j = json.loads(r.read().decode("utf-8"))
            body = j["response"]["body"]
            return body
        except Exception as e:
            print("  다시", t + 1, type(e).__name__, flush=True); time.sleep(3 * (t + 1))
    raise RuntimeError("API 응답 없음")

def fetch(term):
    out, page, n = [], 1, 1000
    while True:
        b = call({"pageNo": page, "numOfRows": n, "cond[BPLC_NM::LIKE]": term, "cond[SALS_STTS_CD::EQ]": "01"})
        items = (b.get("items") or {}).get("item") or []
        if isinstance(items, dict): items = [items]
        out += items
        tot = int(b.get("totalCount", 0))
        if page * n >= tot or not items: break
        page += 1
    print(f"{term}: {len(out)} / {tot}", flush=True)
    return out

recs = {}
for term in QUERIES:
    f = RAW / f"info_{term}.json"
    items = json.loads(f.read_text(encoding="utf-8")) if f.exists() else fetch(term)
    f.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    for it in items: recs[it["MNG_NO"]] = it
print("고유 사업장", len(recs))

# 좌표 변환: 중부원점 TM(Bessel). 어느 정의가 맞는지는 상가정보와 겹치는 정도로 고른다
rows = list(csv.DictReader(open(ROOT / "data" / "stores.csv", encoding="utf-8")))
s_lon = np.array([float(r["lon"]) for r in rows]); s_lat = np.array([float(r["lat"]) for r in rows])
s_br = np.array([brand(r["name"]) for r in rows])
def unit(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
R = 6371.0088

T = [(rec, brand(rec["BPLC_NM"])) for rec in recs.values()]
T = [(r, b) for r, b in T if b != "etc" and r.get("CRD_INFO_X") and r.get("CRD_INFO_Y")]
tx = np.array([float(r["CRD_INFO_X"]) for r, _ in T]); ty = np.array([float(r["CRD_INFO_Y"]) for r, _ in T])
tb = np.array([b for _, b in T])
best = None
for crs in ("EPSG:5174", "EPSG:2097", "EPSG:5181", "EPSG:5186"):
    lon, lat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform(tx, ty)
    ok = np.isfinite(lon) & (lon > 124) & (lon < 132) & (lat > 33) & (lat < 39)
    c, _ = cKDTree(unit(s_lon, s_lat)).query(unit(lon[ok], lat[ok]))
    med = float(np.median(2 * R * np.arcsin(c / 2)) * 1000)
    print(crs, "최근접 상가정보 편의점까지 중앙값", round(med, 1), "m")
    if best is None or med < best[1]: best = (crs, med, lon, lat)
crs, _, t_lon, t_lat = best
print("고른 좌표계", crs)

res = {"crs": crs, "brands": {}}
for b in ("gs", "cu", "se", "e24"):
    sm = s_br == b; tm = (tb == b) & np.isfinite(t_lon)
    if not tm.any(): continue
    tt = cKDTree(unit(t_lon[tm], t_lat[tm]))
    c, _ = tt.query(unit(s_lon[sm], s_lat[sm]))
    d = 2 * R * np.arcsin(np.clip(c / 2, 0, 1)) * 1000
    cov = {f"within_{m}m": round(float((d <= m).mean()) * 100, 1) for m in (30, 50, 100, 200)}
    res["brands"][b] = {"sangga": int(sm.sum()), "tobacco": int(tm.sum()), **cov}
    print(b, res["brands"][b], flush=True)
sm = s_br != "etc"; tm = np.isfinite(t_lon)
c, _ = cKDTree(unit(t_lon[tm], t_lat[tm])).query(unit(s_lon[sm], s_lat[sm]))
d = 2 * R * np.arcsin(np.clip(c / 2, 0, 1)) * 1000
res["all4"] = {"sangga": int(sm.sum()), "tobacco": int(tm.sum()), **{f"within_{m}m": round(float((d <= m).mean()) * 100, 1) for m in (30, 50, 100, 200)}}
print("4대 브랜드 합계", res["all4"])
json.dump(res, open(ROOT / "out" / "tobacco_coverage.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
