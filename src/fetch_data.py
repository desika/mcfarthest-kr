"""원본 데이터 받기 → data/

  1) 소상공인시장진흥공단 상가(상권)정보 전국 파일 (공공데이터포털, 약 350 MB zip) → data/raw/*.csv
  2) 통계청 시도·시군구·읍면동 경계 2013 (southkorea/southkorea-maps)
  3) Natural Earth 10m 육지 경계선 (DMZ 남방한계선)

공공데이터포털 파일은 화면의 다운로드 버튼과 같은 순서로 요청한다: 상세 조회 → 횟수 확인 → 파일.
데이터셋이 새 판으로 바뀌면 상세 페이지의 uddi 값이 달라지므로 UDDI 를 고쳐 쓴다.
"""
import http.cookiejar, json, sys, urllib.parse, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
PK, UDDI = "15083033", "uddi:b3094bc9-8756-4ecc-9141-9144b98a531e"   # 상가(상권)정보 2026-06 판
BASE = "https://www.data.go.kr"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = [("User-Agent", "Mozilla/5.0"), ("Referer", f"{BASE}/data/{PK}/fileData.do")]

def post(path, data):
    req = urllib.request.Request(BASE + path, urllib.parse.urlencode(data).encode(), {"X-Requested-With": "XMLHttpRequest"})
    return op.open(req).read().decode("utf-8")

def get(url, dst):
    if dst.exists(): print("있음", dst.name); return
    print("받는 중", url)
    with op.open(url) as r, open(dst, "wb") as f:
        while chunk := r.read(1 << 20): f.write(chunk)

# 1) 상가정보
z = DATA / "store.zip"
if not z.exists():
    op.open(f"{BASE}/data/{PK}/fileData.do").read()
    info = json.loads(post("/tcs/dss/selectFileDataDownload.do", {"publicDataDetailPk": UDDI, "publicDataPk": PK, "atchFileId": "",
                                                                  "fileDetailSn": "1", "publicDataTyCode": "PR0051"}))
    if not info.get("status"): sys.exit("공공데이터포털 응답이 바뀌었습니다. 상세 페이지에서 직접 받아 data/store.zip 으로 두세요.")
    fid, sn = info["atchFileId"], info["fileDetailSn"]
    post("/cmm/cmm/check-limit.json", {"atchFileId": fid, "fileDetailSn": sn})
    get(f"{BASE}/cmm/cmm/fileDownload.do?atchFileId={fid}&fileDetailSn={sn}&dataNm=store", z)
raw = DATA / "raw"
if not any(raw.glob("*.csv")):
    raw.mkdir(exist_ok=True); zipfile.ZipFile(z).extractall(raw); print("압축 풂", raw)

# 2) 행정구역 경계
SK = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/"
for name, dst in [("skorea_provinces_geo.json", "skorea_provinces_geo.json"), ("skorea_provinces_geo_simple.json", "skorea_provinces_geo_simple.json"),
                  ("skorea_municipalities_geo_simple.json", "muni_simple.json"), ("skorea_submunicipalities_geo_simple.json", "submuni_simple.json")]:
    get(SK + name, DATA / dst)

# 3) DMZ 남방한계선
get("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_boundary_lines_land.geojson", DATA / "ne_bl.geojson")
print("끝")
