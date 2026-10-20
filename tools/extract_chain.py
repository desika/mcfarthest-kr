"""상가정보 원본에서 체인점만 뽑기 → data/chain_<이름>.csv (stores.csv 와 같은 열)

  python tools/extract_chain.py          # mcd · kimbap · paik 한 번에 (원본을 한 번만 훑음)
이름이 흔한 상호(본가·행복분식 등)는 빼고, 음식 업종(상권업종대분류명 '음식')만 남긴다.
"""
import csv, glob, re, sys, collections
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
CHAINS = {
    "mcd": ("McDonald's", re.compile(r"맥도날드|MCDONALD|McDonald", re.I)),
    "kimbap": ("Kimbap Heaven", re.compile(r"김밥천국")),
    # 더본코리아(백종원) 브랜드
    "paik": ("Paik's brands", re.compile(r"빽다방|홍콩반점|새마을식당|한신포차|역전우동|롤링파스타|인생설렁탕|연돈볼카츠|빽보이피자|원조쌈밥집|리춘시장|막이오름|미정국수|고투웍|백철판|돌배기집|백스비빔밥|백's비빔밥")),
}
PAIK_SUB = ["빽다방", "홍콩반점", "새마을식당", "한신포차", "역전우동", "롤링파스타", "인생설렁탕", "연돈볼카츠", "빽보이피자", "원조쌈밥집", "리춘시장", "막이오름", "미정국수", "고투웍", "백철판", "돌배기집"]
out = {k: open(ROOT / "data" / f"chain_{k}.csv", "w", newline="", encoding="utf-8") for k in CHAINS}
W = {k: csv.writer(f) for k, f in out.items()}
for w in W.values(): w.writerow(["name", "branch", "sido", "sigungu", "dong", "addr", "lon", "lat"])
cnt = collections.Counter(); sub = collections.Counter()
for f in sorted(glob.glob(str(ROOT / "data" / "raw" / "*.csv"))):
    with open(f, encoding="utf-8-sig", newline="") as fi:
        for row in csv.DictReader(fi):
            if row["상권업종대분류명"] != "음식": continue
            nm = row["상호명"]
            for k, (_, rx) in CHAINS.items():
                if not rx.search(nm): continue
                try: lon, lat = float(row["경도"]), float(row["위도"])
                except ValueError: continue
                W[k].writerow([nm, row["지점명"], row["시도명"], row["시군구명"], row["법정동명"], row["도로명주소"] or row["지번주소"], lon, lat])
                cnt[k] += 1
                if k == "paik": sub[next((b for b in PAIK_SUB if b in nm), "기타")] += 1
for f in out.values(): f.close()
for k, (label, _) in CHAINS.items(): print(f"{k} {label}: {cnt[k]}")
print("백종원 브랜드별:", sub.most_common())
