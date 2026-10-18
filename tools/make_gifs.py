"""README 용 움짤 만들기 → docs/img/*.gif

완성 페이지에 상태를 바꾸는 짧은 스크립트를 붙여 헤드리스 크롬으로 한 장씩 찍고, Pillow 로 이어 붙인다.
  python tools/make_gifs.py            # 셋 다
  python tools/make_gifs.py grow       # 하나만
"""
import json, math, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PAGE = (ROOT / "out" / "mcfarthest-kr.html").read_text(encoding="utf-8")
SETS = json.load(open(ROOT / "out" / "sets.json", encoding="utf-8"))["sets"]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TMP = Path(tempfile.mkdtemp(prefix="mf_gif_"))

def slider_js(r, rstar):
    v = 1000 * math.log(r / 0.1) / math.log(rstar * 1.25 / 0.1)
    return f'const s=document.getElementById("slider");s.value={v:.4f};s.dispatchEvent(new Event("input"));'

def shoot(args):
    name, js, size, css = args
    html = TMP / f"{name}.html"; png = TMP / f"{name}.png"
    html.write_text('<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0">'
                    + (f"<style>{css}</style>" if css else "") + PAGE
                    + f"<script>setTimeout(()=>{{{js}}},1200)</script></body></html>", encoding="utf-8")
    for _ in range(3):                         # 가끔 크롬이 멈춤 → 다시
        try:
            subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", f"--window-size={size[0]},{size[1]}", "--virtual-time-budget=6000",
                            f"--screenshot={png}", html.as_uri()], capture_output=True, timeout=90)
            if png.exists(): return png
        except subprocess.TimeoutExpired:
            pass
    raise RuntimeError(f"캡처 실패: {name}")

def make(name, frames, size, durations, width, css=""):
    jobs = [(f"{name}_{i:03d}", js, size, css) for i, js in enumerate(frames)]
    with ThreadPoolExecutor(4) as ex: pngs = list(ex.map(shoot, jobs))
    ims = []
    for pth in pngs:
        im = Image.open(pth).convert("RGB")
        if width and im.width != width: im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        ims.append(im.quantize(colors=255, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE))
    out = ROOT / "docs" / "img" / f"{name}.gif"
    ims[0].save(out, save_all=True, append_images=ims[1:], duration=durations, loop=0, optimize=True, disposal=1)
    print(out.name, len(ims), "frames", out.stat().st_size // 1024, "KB", flush=True)

def grow():
    rs = SETS["all"]["results"]["south"]["r"]; n = 40
    radii = [0.1 * (rs / 0.1) ** (i / (n - 1)) for i in range(n)]
    make("grow", [slider_js(r, rs) for r in radii], (1200, 700), [110] * (n - 1) + [2600], 840)

def answer():
    rs = SETS["all"]["results"]["south"]["r"]; n = 26
    radii = [8 + (rs - 8) * (i / (n - 1)) ** 0.8 for i in range(n)]
    # 지도는 그대로 그리게 두고(크기가 0이면 그리기가 멈춤) 정답 부분을 화면 맨 위에 덮어 찍는다
    css = ".wrap{position:absolute!important;inset:0;max-width:none!important;z-index:9;background:var(--bg);padding-top:16px!important;overflow:hidden}.wrap>*{max-width:728px;margin-inline:auto;width:100%}"
    make("answer", [slider_js(r, rs) for r in radii], (860, 900), [130] * (n - 1) + [2600], 760, css)

def brands():
    frames = []
    for b in ["all", "gs", "cu", "se", "e24"]:
        rs = SETS[b]["results"]["south"]["r"]
        frames.append(f'document.querySelector(".brands button[data-b={b}]").click();setTimeout(()=>{{{slider_js(rs, rs)}}},200);')
    make("brands", frames, (1200, 700), [1600] * 5, 960)

todo = sys.argv[1:] or ["grow", "answer", "brands"]
for t in todo: globals()[t]()
