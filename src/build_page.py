"""src/page.html + out/page_data.js · fields.js · sets_fields.js → out/mcfarthest-kr.html (한 파일)"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
html = (ROOT / "src" / "page.html").read_text(encoding="utf-8")
data = "\n".join((ROOT / "out" / f).read_text(encoding="utf-8") for f in ("page_data.js", "fields.js", "sets_fields.js"))
out = ROOT / "out" / "mcfarthest-kr.html"
out.write_text(html.replace("<!--DATA-->", "<script>" + data + "</script>"), encoding="utf-8")
print(out, out.stat().st_size // 1024, "KB")
