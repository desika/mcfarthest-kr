"""전국 '영업/정상' 담배소매점 전부 받기 → data/tobacco/all_open.json, data/tobacco_stores.csv

행정안전부 기타_담배소매업 조회서비스(info), 한 번에 100건까지만 준다. 좌표는 중부원점 TM → 경위도(EPSG:4326).
stores.csv 와 같은 열(name, branch, sido, sigungu, dong, addr, lon, lat)로 저장해 같은 계산 스크립트에 넣을 수 있게 한다.
"""
import csv, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

import numpy as np
from pyproj import Transformer

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
KEY = next(l.split("=", 1)[1].strip() for l in open(ROOT / ".env", encoding="utf-8") if l.startswith("DATA_GO_KR_KEY="))
URL = "https://apis.data.go.kr/1741000/tobacco_retailers/info"
RAW = ROOT / "data" / "tobacco"; RAW.mkdir(parents=True, exist_ok=True)

PER = 100                                    # API 가 한 번에 주는 최대 건수

def call(page, n=PER):
    q = {"serviceKey": KEY, "returnType": "json", "pageNo": page, "numOfRows": n, "cond[SALS_STTS_CD::EQ]": "01"}
    for t in range(5):
        try:
            with urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))["response"]["body"]
        except Exception as e:
            print("  다시", page, t + 1, type(e).__name__, flush=True); time.sleep(4 * (t + 1))
    raise RuntimeError(f"{page}쪽 응답 없음")

import concurrent.futures as cf
first = call(1); tot = int(first["totalCount"]); pages = (tot + PER - 1) // PER
print("영업 중 담배소매점", tot, "→", pages, "쪽", flush=True)
items = list((first.get("items") or {}).get("item") or [])
def page_items(p):
    it = (call(p).get("items") or {}).get("item") or []
    return [it] if isinstance(it, dict) else it
with cf.ThreadPoolExecutor(4) as ex:                 # 4개씩 동시에
    for k, got in enumerate(ex.map(page_items, range(2, pages + 1)), 2):
        items += got
        if k % 100 == 0: print(f"  {k}/{pages} · {len(items)}", flush=True)
(RAW / "all_open.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")

ok = [r for r in items if r.get("CRD_INFO_X") and r.get("CRD_INFO_Y")]
x = np.array([float(r["CRD_INFO_X"]) for r in ok]); y = np.array([float(r["CRD_INFO_Y"]) for r in ok])
lon, lat = Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True).transform(x, y)
inside = (lon > 124) & (lon < 132) & (lat > 33) & (lat < 39)
with open(ROOT / "data" / "tobacco_stores.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["name", "branch", "sido", "sigungu", "dong", "addr", "lon", "lat"])
    for r, lo, la, k in zip(ok, lon, lat, inside):
        if not k: continue
        a = (r.get("ROAD_NM_ADDR") or r.get("LOTNO_ADDR") or "").split()
        w.writerow([r["BPLC_NM"], "", a[0] if a else "", a[1] if len(a) > 1 else "", a[2] if len(a) > 2 else "", " ".join(a), round(float(lo), 7), round(float(la), 7)])
print("좌표 있는 곳", len(ok), "· 국내 좌표", int(inside.sum()), "→ data/tobacco_stores.csv", flush=True)
