"""src/page.html + out/page_data.js · fields.js · sets_fields.js + src/i18n.js → out/mcfarthest-kr.html (한 파일)

MF_DATASET=tobacco 이면 담배소매점 판 → out/mcfarthest-kr_tobacco.html (전국 거리장 없이 화면 거리장만)
"""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DATASET = os.environ.get("MF_DATASET", "cvs"); SUF = "" if DATASET == "cvs" else "_" + DATASET
html = (ROOT / "src" / "page.html").read_text(encoding="utf-8")
files = [f"page_data{SUF}.js"] + (["fields.js"] if DATASET == "cvs" else []) + [f"sets_fields{SUF}.js"]
data = "\n".join((ROOT / "out" / f).read_text(encoding="utf-8") for f in files)
data += "\n" + (ROOT / "src" / "i18n.js").read_text(encoding="utf-8")      # 7개 언어 문구 + 로마자 변환
out = ROOT / "out" / f"mcfarthest-kr{SUF}.html"
out.write_text(html.replace("<!--DATA-->", "<script>" + data + "</script>"), encoding="utf-8")
print(out, out.stat().st_size // 1024, "KB")
