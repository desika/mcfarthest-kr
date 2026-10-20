"""카카오 로컬 키워드 검색으로 체인 전 매장 받기 → data/chain_<이름>.csv

  python tools/kakao_chain.py mcd 맥도날드 맥도날드 맥도날드     # 이름 · 검색어 · 상호에 들어갈 말 · 업종 분류에 들어갈 말
카카오는 한 번에 최대 45곳(15곳 × 3쪽)만 준다 → 한국을 사각형으로 나눠 검색하고,
45곳이 꽉 찬 사각형은 4등분해 다시 검색한다. 상호에 검색어가 들어간 곳만 남긴다.
키는 이 프로젝트 .env 의 KAKAO_REST_KEY (값은 출력하지 않음, .env 는 git 에 안 올라감).
"""
import csv, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
KEY = None
for envf in [ROOT / ".env"]:
    if envf.exists():
        for l in open(envf, encoding="utf-8"):
            if l.startswith("KAKAO_REST_KEY="): KEY = l.split("=", 1)[1].strip().strip('"\'')
    if KEY: break
name, query = sys.argv[1], sys.argv[2]
must = sys.argv[3] if len(sys.argv) > 3 else query
URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
calls = 0

def search(rect):
    global calls
    out = []
    for page in (1, 2, 3):
        q = {"query": query, "rect": ",".join(f"{v:.6f}" for v in rect), "page": page, "size": 15}
        req = urllib.request.Request(URL + "?" + urllib.parse.urlencode(q), headers={"Authorization": f"KakaoAK {KEY}"})
        for t in range(4):
            try:
                with urllib.request.urlopen(req, timeout=30) as r: j = json.loads(r.read().decode("utf-8")); break
            except Exception as e:
                time.sleep(2 * (t + 1))
        else:
            raise RuntimeError("카카오 응답 없음")
        calls += 1
        out += j["documents"]
        if j["meta"]["is_end"]: break
    return out, len(out) >= 45

found = {}
def walk(x0, y0, x1, y1, depth=0):
    docs, full = search((x0, y0, x1, y1))
    if full and depth < 8:
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        for r in ((x0, y0, xm, ym), (xm, y0, x1, ym), (x0, ym, xm, y1), (xm, ym, x1, y1)): walk(*r, depth + 1)
    else:
        for d in docs: found[d["id"]] = d

# 한국을 1° 칸으로
for lo in range(124, 132):
    for la in range(33, 39):
        walk(lo, la, lo + 1, la + 1)
cat = sys.argv[4] if len(sys.argv) > 4 else None          # 카카오 업종 분류에 들어가야 할 말 (예: 맥도날드)
rows = [d for d in found.values() if must.replace(" ", "") in d["place_name"].replace(" ", "")
        and (cat is None or cat in d.get("category_name", ""))]
import collections; print("업종 분류 상위", collections.Counter(d.get("category_name", "") for d in found.values()).most_common(6))
with open(ROOT / "data" / f"chain_{name}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["name", "branch", "sido", "sigungu", "dong", "addr", "lon", "lat"])
    for d in rows:
        a = (d.get("road_address_name") or d.get("address_name") or "").split()
        w.writerow([d["place_name"], "", a[0] if a else "", a[1] if len(a) > 1 else "", a[2] if len(a) > 2 else "", " ".join(a), d["x"], d["y"]])
print(f"{name}: 검색 결과 {len(found)} · 상호에 '{must}' 포함 {len(rows)} · 호출 {calls}번")
