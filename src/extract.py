"""상가정보 CSV 에서 편의점만 뽑아 stores.csv 로 저장"""
import csv, glob, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
out = ROOT / "data" / "stores.csv"
cats = collections.Counter(); brands = collections.Counter(); n = 0
with open(out, "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo); w.writerow(["name", "branch", "sido", "sigungu", "dong", "addr", "lon", "lat"])
    for f in sorted(glob.glob(str(ROOT / "data" / "raw" / "*.csv"))):
        with open(f, encoding="utf-8-sig", newline="") as fi:
            r = csv.DictReader(fi)
            for row in r:
                sub = row["상권업종소분류명"]
                if "편의점" in sub: cats[sub] += 1
                if sub != "편의점": continue
                try: lon, lat = float(row["경도"]), float(row["위도"])
                except ValueError: continue
                w.writerow([row["상호명"], row["지점명"], row["시도명"], row["시군구명"], row["법정동명"],
                            row["도로명주소"] or row["지번주소"], lon, lat])
                brands[row["상호명"].split()[0][:8]] += 1; n += 1
print("편의점", n); print(cats); print(brands.most_common(12))
