"""인스타 릴스 영상 만들기 → out/reels/<이름>.mp4

  python tools/make_reel.py farthest      # 편의점에서 가장 먼 곳
  python tools/make_reel.py brands        # 브랜드 대결

순서
  1) 문장마다 영어 음성(edge-tts)을 따로 만들어 길이를 잰다 → 말하는 시각이 정확히 나온다
  2) 그 시각에 맞춰 프레임마다 반지름·시점·브랜드를 정하고, 지도 페이지를 1080×1920 으로 띄워 한 장씩 찍는다
  3) ffmpeg 로 그림 + 음성 → H.264 MP4 (릴스 규격 9:16, 30fps)
화면 글자는 인스타 위·아래 UI 에 가리지 않는 가운데 영역에 둔다.
"""
import asyncio, json, math, re, shutil, subprocess, sys, tempfile
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "out" / "mcfarthest-kr.html"
OUT = ROOT / "out" / "reels"; OUT.mkdir(parents=True, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
SETS = json.load(open(ROOT / "out" / "sets.json", encoding="utf-8"))["sets"]
VOICE, FPS, W, H = "en-US-AvaNeural", 30, 540, 960     # CSS 크기, 2배로 찍어 1080×1920
LEAD, GAP, TAIL = 0.5, 0.35, 3.2                          # 시작 여백 · 문장 사이 · 끝 화면

# ── 음성 ──
# 영어 목소리가 한국 지명을 철자대로 읽지 않게 소리 나는 대로 바꿔 읽힘 (자막은 그대로)
PRON = {"myeon": "myun", "gun": "goon", "gu": "goo", "si": "shee", "eup": "up", "ri": "ree", "daesil": "deh-shil", "Uiseong": "Wee-sung", "Chunsan": "Choon-sahn", "Daehak": "Deh-hahk", "Sillim": "Shil-lim", "gosichon": "go-shee-chon", "Gosichon": "Go-shee-chon",
        "Gwanaksan": "Gwah-nahk-sahn", "Gwacheon": "Gwah-chun", "Anyang": "Ahn-yahng", "Gumi": "Goo-mee", "Wonpyeong": "Won-pyung", "hagwons": "hahg-wons", "hagwon": "hahg-won", "Daechi": "Deh-chee", "Gyeonggi": "Gyung-gee", "Dasan": "Dah-sahn",
        "Daegu": "Deh-goo", "Beomeo": "Bum-uh", "Busan": "Boo-sahn", "Haeundae": "Heh-oon-deh", "Myeongji": "Myung-jee",
        "Gangnam": "Gahng-nahm", "Namyangju": "Nahm-yahng-joo", "Suseong": "Soo-sung", "Gangseo": "Gahng-suh", "Uljin": "Ool-jin",
        "Jeju": "Jeh-joo", "Gwanak": "Gwah-nahk", "Uiseong": "Wee-sung", "Yeongyang": "Yung-yahng", "Sinan": "Shin-ahn",
        "Hwacheon": "Hwah-chun", "Gyeongbuk": "Gyung-book"}
SINO = "il i sam sah oh yook chil pal goo".split()
def speakable(text):
    for k in sorted(SAY, key=len, reverse=True): text = text.replace(k, SAY[k])
    text = re.sub(r"(\d)-dong", lambda m: " " + SINO[int(m.group(1)) - 1] + "-dong", text)
    return re.sub(r"[A-Za-z]+", lambda m: PRON.get(m.group(0), m.group(0)), text)
async def _tts(text, path, voice=None):
    await edge_tts.Communicate(speakable(text), voice or VOICE, rate="-4%").save(str(path))
def duration(path):
    r = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)
def narrate(lines, work, voice=None, lead=None):
    clips, t = [], (lead if lead is not None else LEAD)
    for i, ln in enumerate(lines):
        p = work / f"v{i:02d}.mp3"; asyncio.run(_tts(ln["say"], p, voice)); d = duration(p)
        clips.append({**ln, "file": p, "t0": t, "t1": t + d}); t += d + GAP
    total = t - GAP + TAIL
    # 문장들을 시각에 맞춰 한 트랙으로
    inputs, filt = [], []
    for i, c in enumerate(clips):
        inputs += ["-i", str(c["file"])]; filt.append(f"[{i}:a]adelay={int(c['t0'] * 1000)}|{int(c['t0'] * 1000)}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(clips))) + f"amix=inputs={len(clips)}:normalize=0,apad,atrim=0:{total:.3f}[out]"
    audio = work / "voice.m4a"
    subprocess.run([FF, "-y", *inputs, "-filter_complex", ";".join(filt) + ";" + mix, "-map", "[out]", "-c:a", "aac", "-b:a", "160k", str(audio)],
                   check=True, capture_output=True)
    return clips, total, audio

# ── 화면 ──
REEL_CSS = """
html, body { overflow: hidden !important; }
.stage { position: fixed !important; inset: 0 !important; height: 100vh !important; max-width: none !important; padding: 0 !important; display: block !important; }
.stage .head, .stage .panel, .recenter, .map .tag, .map .credit, .pop, .tip, .wrap { display: none !important; }
.map { position: fixed !important; inset: 0 !important; width: 100vw !important; height: 100vh !important; border: 0 !important; border-radius: 0 !important; }
#reel { position: fixed; inset: 0; z-index: 20; pointer-events: none; font-family: "Noto Sans", "Space Grotesk", sans-serif; color: #e6eef0; }
#reel .band-t { position: absolute; left: 0; right: 0; top: 0; height: 360px; background: linear-gradient(#080c0efa 0%, #080c0ef2 72%, #080c0e00 100%); }
#reel .band-b { position: absolute; left: 0; right: 0; bottom: 0; height: 430px; background: linear-gradient(#080c0e00 0%, #080c0ed9 45%, #080c0ef7 100%); }
#reel .eyebrow { position: absolute; left: 34px; top: 118px; font: 600 13px "Space Grotesk", sans-serif; letter-spacing: .16em; color: #84969b; }
#reel .title { position: absolute; left: 34px; right: 34px; top: 140px; font: 800 33px/1.12 "Noto Sans", sans-serif; letter-spacing: -.01em; }
#reel .title b { background: linear-gradient(90deg, #3d8bff, #5fe3c6); -webkit-background-clip: text; background-clip: text; color: transparent; }
#reel .rad { position: absolute; left: 34px; top: 236px; font: 700 54px/1 "Space Grotesk", sans-serif; color: #5fe3c6; }
#reel .rad small { font-size: 22px; color: #84969b; margin-left: 6px; font-weight: 500; }
#reel .cov { position: absolute; left: 34px; top: 298px; font: 500 18px "Noto Sans", sans-serif; color: #e6eef0; }
#reel .cov b { font: 700 21px "Space Grotesk", sans-serif; }
#reel .cap { position: absolute; left: 30px; right: 30px; top: 676px; text-align: center; font: 700 27px/1.28 "Noto Sans", sans-serif; text-shadow: 0 2px 14px #000; }
#reel .tag { position: absolute; left: 34px; top: 548px; font: 600 15px "Space Grotesk", sans-serif; letter-spacing: .12em; color: #5fe3c6; text-shadow: 0 1px 8px #000; }
#reel svg { position: absolute; inset: 0; width: 100%; height: 100%; }
#reel .end { position: absolute; inset: 0; background: #080c0ee6; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 14px; text-align: center; padding: 0 40px; opacity: 0; }
#reel .end .big { font: 700 88px/1 "Space Grotesk", sans-serif; color: #5fe3c6; }
#reel .end .t1 { font: 700 26px/1.25 "Noto Sans", sans-serif; }
#reel .end .t2 { font: 500 17px/1.4 "Noto Sans", sans-serif; color: #84969b; margin-top: 18px; }
#reel .end .url { font: 600 17px "Space Grotesk", sans-serif; color: #e6eef0; }
/* 표지: 첫 1.4초. 큰 숫자 하나 + 한 줄 */
#reel .cover { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center; gap: 12px; padding: 0 40px 120px; opacity: 0;
  background: radial-gradient(120% 70% at 50% 45%, #080c0e99 0%, #080c0ef2 70%); }
#reel .cover .k { font: 600 14px "Space Grotesk", sans-serif; letter-spacing: .28em; color: #5fe3c6; }
#reel .cover .big { font: 700 132px/0.92 "Space Grotesk", sans-serif; letter-spacing: -.03em; background: linear-gradient(90deg, #3d8bff, #5fe3c6); -webkit-background-clip: text; background-clip: text; color: transparent; }
#reel .cover .t { font: 800 38px/1.1 "Noto Sans", sans-serif; }
#reel .cover .s { font: 500 18px/1.35 "Noto Sans", sans-serif; color: #b9c6c9; margin-top: 6px; }
/* 순위 카드 */
#reel .rank { position: absolute; left: 24px; width: 268px; top: 252px; display: flex; flex-direction: column; gap: 7px; opacity: 0; }
#reel .rank .row { display: grid; grid-template-columns: 26px 1fr auto; gap: 10px; align-items: center; padding: 8px 12px; border-radius: 10px; background: #080c0ed9; border: 1px solid #ffffff1f; }
#reel .rank .row .no { font: 700 18px "Space Grotesk", sans-serif; color: #5fe3c6; }
#reel .rank .row .nm { font: 700 17px "Noto Sans", sans-serif; }
#reel .rank .row .nm span { display: block; font: 500 12px "Noto Sans", sans-serif; color: #9fb0b4; }
#reel .rank .row .v { font: 700 22px "Space Grotesk", sans-serif; }
#reel .rank .row .bar { grid-column: 1 / -1; height: 4px; border-radius: 2px; background: linear-gradient(90deg, #3d8bff, #5fe3c6); }

/* ── 샤넬: 흑백 · 세리프 · 넓은 자간 ── */
body.th-chanel .map canvas { filter: grayscale(1) contrast(1.3) brightness(1.08); }
body.th-chanel #reel { color: #f4f2ee; }
body.th-chanel #reel .band-t { background: linear-gradient(#000 0%, #000000ee 72%, #0000 100%); }
body.th-chanel #reel .band-b { background: linear-gradient(#0000 0%, #000000dd 45%, #000 100%); }
body.th-chanel #reel .eyebrow { font: 500 11px "Montserrat", sans-serif; letter-spacing: .46em; color: #c9c6bf; }
body.th-chanel #reel .title { font: 600 36px/1.08 "Playfair Display", serif; }
body.th-chanel #reel .title b { background: none; -webkit-text-fill-color: #fff; color: #fff; font-style: italic; font-weight: 600; }
body.th-chanel #reel .rad { font: 500 56px/1 "Playfair Display", serif; color: #fff; }
body.th-chanel #reel .rad small, body.th-chanel #reel .cov { font-family: "Montserrat", sans-serif; color: #d8d5ce; }
body.th-chanel #reel .cap { font: 500 24px/1.32 "Montserrat", sans-serif; letter-spacing: .01em; }
body.th-chanel #reel .cover { background: radial-gradient(120% 70% at 50% 45%, #00000099 0%, #000000f5 70%); align-items: center; text-align: center; }
body.th-chanel #reel .cover .k { font: 500 12px "Montserrat", sans-serif; letter-spacing: .6em; color: #d8d5ce; border-top: 1px solid #fff6; border-bottom: 1px solid #fff6; padding: 10px 0 10px .6em; }
body.th-chanel #reel .cover .big { font: 500 150px/0.95 "Playfair Display", serif; background: none; -webkit-text-fill-color: #fff; color: #fff; letter-spacing: -.02em; }
body.th-chanel #reel .cover .t { font: italic 600 40px/1.1 "Playfair Display", serif; }
body.th-chanel #reel .cover .s { font: 500 13px "Montserrat", sans-serif; letter-spacing: .38em; text-transform: uppercase; color: #bdbab3; }
body.th-chanel #reel .rank .row { background: #000000e0; border-color: #ffffff33; border-radius: 0; }
body.th-chanel #reel .rank .row .no, body.th-chanel #reel .rank .row .v { font-family: "Playfair Display", serif; color: #fff; }
body.th-chanel #reel .rank .row .nm { font-family: "Montserrat", sans-serif; font-weight: 600; letter-spacing: .02em; }
body.th-chanel #reel .rank .row .bar { background: #fff; height: 2px; }
body.th-chanel #reel .end { background: #000000f2; }
body.th-chanel #reel .end .big { font: 500 96px/1 "Playfair Display", serif; color: #fff; }
body.th-chanel #reel .end .t1 { font: italic 600 26px/1.25 "Playfair Display", serif; }

/* ── 가을: 단풍 주황 · 호박 ── */
body.th-autumn .map canvas { filter: hue-rotate(218deg) saturate(1.7) brightness(1.02); }
body.th-autumn #reel .band-t { background: linear-gradient(#120a05fa 0%, #120a05f0 72%, #120a0500 100%); }
body.th-autumn #reel .band-b { background: linear-gradient(#120a0500 0%, #120a05d9 45%, #120a05f7 100%); }
body.th-autumn #reel .eyebrow { color: #d9a27a; }
body.th-autumn #reel .title b, body.th-autumn #reel .cover .big { background: linear-gradient(90deg, #ff5f3a, #ffc14d); -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-fill-color: transparent; }
body.th-autumn #reel .cover { background: radial-gradient(120% 70% at 50% 45%, #120a0599 0%, #120a05f5 70%); }
body.th-autumn #reel .cover .k, body.th-autumn #reel .rank .row .no, body.th-autumn #reel .tag { color: #ffb347; }
body.th-autumn #reel .rank .row { background: #1a0e07e0; border-color: #ffb34733; }
body.th-autumn #reel .rank .row .bar { background: linear-gradient(90deg, #ff5f3a, #ffc14d); }
body.th-autumn #reel .end { background: #120a05f0; }
body.th-autumn #reel .end .big { color: #ffb347; }

/* ── 테슬라: 검정 · 가는 산세리프 · 빨강 하나 ── */
body.th-tesla .map canvas { filter: hue-rotate(186deg) saturate(1.6) brightness(.92); }
body.th-tesla #reel { font-family: "Inter", sans-serif; }
body.th-tesla #reel .band-t { background: linear-gradient(#000 0%, #000000ee 72%, #0000 100%); }
body.th-tesla #reel .band-b { background: linear-gradient(#0000 0%, #000000dd 45%, #000 100%); }
body.th-tesla #reel .eyebrow { font: 500 11px "Inter", sans-serif; letter-spacing: .34em; color: #8d8d8d; }
body.th-tesla #reel .title { font: 300 34px/1.12 "Inter", sans-serif; letter-spacing: -.015em; }
body.th-tesla #reel .title b { background: none; -webkit-text-fill-color: #e82127; color: #e82127; font-weight: 600; }
body.th-tesla #reel .rad { font: 200 68px/1 "Inter", sans-serif; color: #fff; letter-spacing: -.03em; }
body.th-tesla #reel .rad small { font-family: "Inter", sans-serif; font-weight: 300; }
body.th-tesla #reel .cov { font-family: "Inter", sans-serif; font-weight: 300; }
body.th-tesla #reel .cov b { font-family: "Inter", sans-serif; font-weight: 600; color: #e82127; }
body.th-tesla #reel .cap { font: 400 25px/1.3 "Inter", sans-serif; }
body.th-tesla #reel .tag { font-family: "Inter", sans-serif; color: #e82127; }
body.th-tesla #reel .cover { background: radial-gradient(120% 70% at 50% 45%, #00000080 0%, #000000f5 70%); }
body.th-tesla #reel .cover .k { font: 500 12px "Inter", sans-serif; letter-spacing: .42em; color: #e82127; }
body.th-tesla #reel .cover .big { font: 200 168px/0.9 "Inter", sans-serif; background: none; -webkit-text-fill-color: #fff; color: #fff; letter-spacing: -.06em; }
body.th-tesla #reel .cover .big i { font-style: normal; font-size: .3em; color: #e82127; -webkit-text-fill-color: #e82127; letter-spacing: 0; margin-left: 8px; }
body.th-tesla #reel .cover .t { font: 300 34px/1.12 "Inter", sans-serif; }
body.th-tesla #reel .cover .s { font: 400 14px "Inter", sans-serif; letter-spacing: .3em; text-transform: uppercase; color: #8d8d8d; }
body.th-tesla #reel .rank .row { background: #000000e6; border-color: #ffffff1a; border-radius: 4px; }
body.th-tesla #reel .rank .row .no { color: #e82127; font-family: "Inter", sans-serif; }
body.th-tesla #reel .rank .row .v { font-family: "Inter", sans-serif; font-weight: 300; }
body.th-tesla #reel .rank .row .bar { background: #e82127; height: 2px; }
body.th-tesla #reel .end { background: #000000f2; }
body.th-tesla #reel .end .big { font: 200 104px/1 "Inter", sans-serif; color: #e82127; letter-spacing: -.04em; }
body.th-tesla #reel .end .t1 { font: 300 26px/1.25 "Inter", sans-serif; }
"""
REEL_HTML = """<div id="reel"><div class="band-t"></div><div class="band-b"></div>
<div class="eyebrow" id="r-eye"></div><div class="title" id="r-title"></div>
<div class="rad" id="r-rad"></div><div class="cov" id="r-cov"></div><div class="tag" id="r-tag"></div>
<svg id="r-svg" viewBox="0 0 540 960"></svg><div class="cap" id="r-cap"></div>
<div class="rank" id="r-rank"></div>
<div class="cover" id="r-cover"><div class="k" id="c-k"></div><div class="big" id="c-big"></div><div class="t" id="c-t"></div><div class="s" id="c-s"></div></div>
<div class="end" id="r-end"><div class="big" id="e-big"></div><div class="t1" id="e-t1"></div><div class="t2" id="e-t2"></div><div class="url">desika.github.io/mcfarthest-kr</div></div></div>"""
FRAME_JS = """(p) => {
  const st = MF.st;
  if (p.brand && st.b !== p.brand) MF.setBrand(p.brand);
  if (p.region && st.k !== p.region) st.k = p.region;
  st.r = p.r; st.cam = p.cam; MF.render();
  const $ = id => document.getElementById(id);
  $("r-eye").textContent = p.eye; $("r-title").innerHTML = p.title;
  const r = p.r, rs = r < 1 ? r.toFixed(2) : r < 10 ? r.toFixed(1) : r.toFixed(1);
  $("r-rad").innerHTML = p.showRad ? `r = ${rs}<small>km</small>` : "";
  const c = Math.min(100, MF.cov(r) * 100);
  $("r-cov").innerHTML = p.showRad ? `<b>${c >= 99.95 && r < MF.res().r ? "99.9" : c.toFixed(1)}%</b> ${p.covText || "of the land has a store this close"}` : "";
  $("r-tag").textContent = p.tag || "";
  $("r-cap").textContent = p.cap || ""; $("r-cap").style.top = (p.capTop || 676) + "px";
  // 결정적인 점포들의 원 (확대 장면에서만)
  let svg = "";
  if (p.keys && st.cam) {
    const cam = st.cam, res = MF.res(), fx = 0.8090169943749475 / Math.cos(res.lat * Math.PI / 180);
    const sx = (x) => (x - cam.cx) * cam.s + 270, sy = (y) => (y - cam.cy) * cam.s + 480;
    const rr = Math.min(r, res.r);
    for (const so of res.stores.slice(0, 3)) {
      svg += `<ellipse cx="${sx(so.xy[0])}" cy="${sy(so.xy[1])}" rx="${rr * cam.s * fx}" ry="${rr * cam.s}" fill="none" stroke="#fff" stroke-width="2.2" opacity="${p.keys}"/>`;
      svg += `<circle cx="${sx(so.xy[0])}" cy="${sy(so.xy[1])}" r="5" fill="#5fe3c6" opacity="${p.keys}"/>`;
    }
  }
  $("r-svg").innerHTML = svg;
  const th = "th-" + (p.theme || "dark"); if (document.body.dataset.th !== th) { document.body.classList.remove("th-dark", "th-chanel", "th-tesla", "th-autumn"); document.body.classList.add(th); document.body.dataset.th = th; }
  const cv = $("r-cover"); cv.style.opacity = p.cover || 0;
  if (p.coverText && cv.dataset.done !== "1") { $("c-k").innerHTML = p.coverText[0]; $("c-big").innerHTML = p.coverText[1]; $("c-t").innerHTML = p.coverText[2]; $("c-s").innerHTML = p.coverText[3]; cv.dataset.done = "1"; }
  const rk = $("r-rank"); rk.style.opacity = p.rankOp || 0;
  if (!p.rank) { rk.innerHTML = ""; rk.dataset.k = ""; }
  if (p.rank) {
    const mx = Math.max(...p.rank.map(x => x.n)), key = p.rankN + "|" + p.rank.length;
    if (rk.dataset.k !== key) {
      rk.innerHTML = p.rank.map((x, i) => `<div class="row" style="opacity:${i < p.rankN ? 1 : 0};transform:translateX(${i < p.rankN ? 0 : 30}px);transition:all .35s"><div class="no">${i + 1}</div><div class="nm">${x.a}<span>${x.b}</span></div><div class="v">${x.n.toLocaleString("en-US")}</div><div class="bar" style="width:${(x.n / mx * 100).toFixed(1)}%"></div></div>`).join("");
      rk.dataset.k = key;
    }
  }
  const e = $("r-end"); e.style.opacity = p.end || 0;
  if (p.endText) { $("e-big").textContent = p.endText[0]; $("e-t1").textContent = p.endText[1]; $("e-t2").textContent = p.endText[2]; }
}"""

def ease(t): return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))
COVER_T = 1.45                                              # 표지 장면 길이 (그 뒤 0.35초 동안 사라짐)
def cover_state(t, look):
    if not look.get("cover"): return {"theme": look.get("theme", "dark")}
    op = 1.0 if t < COVER_T else max(0.0, 1 - (t - COVER_T) / 0.35)
    return {"theme": look.get("theme", "dark"), "cover": round(op, 3), "coverText": look["cover"]}
def lerp_log(a, b, t): return math.exp(math.log(a) + (math.log(b) - math.log(a)) * t)

def capture(name, frames_fn, total, audio, work, page=PAGE):
    frames = work / "f"; frames.mkdir()
    n = int(total * FPS)
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome", args=["--hide-scrollbars"])
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.goto(page.as_uri() + "#en")
        pg.add_style_tag(content=REEL_CSS)
        pg.add_style_tag(url="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;1,600&family=Montserrat:wght@400;500;600&family=Inter:wght@200;300;400;600&display=swap")
        pg.evaluate("h => document.body.insertAdjacentHTML('beforeend', h)", REEL_HTML)
        pg.evaluate("() => window.dispatchEvent(new Event('resize'))")
        pg.wait_for_function("() => window.MF && MF.ready()", timeout=60000)
        pg.evaluate("() => document.fonts.ready.then(() => 1)")
        pg.wait_for_timeout(1500)
        # 미리 한 번 훑어 지도 타일을 받아 둔다
        for i in range(0, n, 6):
            pg.evaluate(FRAME_JS, frames_fn(i / FPS))
            if i % 60 == 0: pg.wait_for_timeout(400)
        for _ in range(40):
            if pg.evaluate("() => MF.tilesPending()") == 0: break
            pg.wait_for_timeout(500)
        for i in range(n):
            pg.evaluate(FRAME_JS, frames_fn(i / FPS))
            pg.screenshot(path=str(frames / f"{i:05d}.jpg"), type="jpeg", quality=93)
            if i % 150 == 0: print(f"  {i}/{n}", flush=True)
        br.close()
    mp4 = OUT / f"{name}.mp4"
    subprocess.run([FF, "-y", "-framerate", str(FPS), "-i", str(frames / "%05d.jpg"), "-i", str(audio),
                    "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "24", "-preset", "slow", "-tune", "animation",
                    "-r", str(FPS), "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(mp4)], check=True, capture_output=True)
    # 미리보기 장면 몇 장
    shutil.copy(frames / f"{min(n - 1, int(FPS * 0.7)):05d}.jpg", OUT / f"{name}_cover.jpg")   # 릴스 표지 = 표지 장면
    for k, t in enumerate([0.3, 0.55, 0.8, 0.97]):
        shutil.copy(frames / f"{int(n * t):05d}.jpg", OUT / f"{name}_preview{k}.jpg")
    print(mp4, round(mp4.stat().st_size / 1e6, 1), "MB", round(total, 1), "s", flush=True)
    return mp4

# ── 편: 편의점에서 가장 먼 곳 ──
def farthest():
    res = SETS["all"]["results"]["south"]; rs = res["r"]
    return fly_story("farthest", PAGE, res, lines=[
        {"say": "South Korea has fifty-four thousand convenience stores.", "cap": "South Korea has 54,446 convenience stores."},
        {"say": "Draw a circle around every single one, and let them grow.", "cap": "Draw a circle around every one. Let them grow."},
        {"say": "At one kilometer, almost all of Seoul is covered.", "cap": "At 1 km, almost all of Seoul is covered."},
        {"say": "At five kilometers, three quarters of the country.", "cap": "At 5 km, three quarters of the country."},
        {"say": "Keep growing, and the gaps close one by one.", "cap": "Keep growing. The gaps close one by one."},
        {"say": "The very last spot is here, in the mountains of Uljin.", "cap": "The very last spot: the mountains of Uljin."},
        {"say": "Nineteen point eight kilometers from the nearest store.", "cap": "19.8 km from the nearest store."},
        {"say": "That's as far as you can get.", "cap": "That's as far as you can get."},
    ], radii=[0.1, 0.28, 0.9, 2.6, 5.0, 13.5, rs, rs, rs, rs], eye="SOUTH KOREA · 54,446 STORES",
       title="How far can you get from a <b>convenience store</b>?", cov_text=None,
       end_text=[f"{rs:.2f} km", "The farthest you can get from a convenience store in South Korea", "Subi-myeon, Uljin · exactly as far from three stores"])

def fly_story(name, page, res, lines, radii, eye, title, cov_text, end_text, fly=5, base_cam=None, region=None, look=None):
    """원이 자라다 fly 번째 문장에서 정답 지점으로 날아가는 이야기.
    base_cam 을 주면 그 시점에 고정해 원을 키운다(서울편). 없으면 서울→전국 자동 시점."""
    rs = res["r"]; look = look or {}
    work = Path(tempfile.mkdtemp(prefix="reel_"))
    clips, total, audio = narrate(lines, work, look.get("voice"), look.get("lead"))
    T = [c["t0"] for c in clips] + [clips[-1]["t1"], total]
    assert len(radii) == len(T), (len(radii), len(T))
    kmx, kmy = 111.320 * 0.8090169943749475, 110.95
    tx, ty = (res["lon"] - 124.55) * kmx, (38.68 - res["lat"]) * kmy
    s_t = W / (rs * 5.4)                                               # 세 원이 다 들어오는 축척
    target = {"s": s_t, "cx": tx, "cy": ty + (480 - 505) / s_t}      # 정답 점을 글자와 자막 사이에
    nat = {}
    def at(t):
        k = max(0, min(len(T) - 2, next((i for i in range(len(T) - 1) if T[i] <= t < T[i + 1]), len(T) - 2)))
        u = (t - T[k]) / max(1e-6, T[k + 1] - T[k])
        r = lerp_log(radii[k], radii[k + 1], ease(u))
        if t < T[0]: r = radii[0]
        cap = next((c["cap"] for c in clips if c["t0"] - 0.15 <= t <= c["t1"] + GAP * 0.8), "")
        cam, keys = base_cam, 0
        if t >= T[fly]:                                                 # 정답 문장부터 그 지점으로
            u2 = ease((t - T[fly]) / (T[fly + 1] - T[fly]))
            a = nat["cam"]
            cam = {"s": lerp_log(a["s"], target["s"], u2), "cx": a["cx"] + (target["cx"] - a["cx"]) * u2, "cy": a["cy"] + (target["cy"] - a["cy"]) * u2}
            keys = round(u2, 3)
        end = ease((t - (total - TAIL + 0.4)) / 0.8) if t > total - TAIL + 0.4 else 0
        return {"r": r, "cam": cam, "keys": keys, "eye": eye, "showRad": True, "covText": cov_text, "region": region,
                "title": title, "cap": cap, "end": end, "endText": end_text, **cover_state(t, look)}
    if base_cam: nat["cam"] = base_cam
    else:                                                               # 날아가기 직전의 전국 시점을 페이지에서 받아 둔다
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="chrome"); pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
            pg.goto(page.as_uri() + "#en"); pg.add_style_tag(content=REEL_CSS); pg.evaluate("() => window.dispatchEvent(new Event('resize'))")
            pg.wait_for_function("() => window.MF && MF.ready()", timeout=60000)
            nat["cam"] = pg.evaluate("r => MF.camera(r)", radii[fly]); br.close()
    return capture(name, at, total, audio, work, page)

# ── 에피소드 틀: tools/episodes.json 한 항목 → 영상 + 본문 ──
def romanize(place):
    """한글 지명 → 로마자 (페이지와 같은 src/i18n.js 변환기를 node 로)"""
    js = (ROOT / "src" / "i18n.js").as_posix()
    code = f"global.window=global;require({json.dumps(js)});process.stdout.write(romPlace(process.argv[1]))"
    r = subprocess.run(["node", "-e", code, place], capture_output=True, text=True, encoding="utf-8")
    out = r.stdout.strip() or place
    SAY[out] = hangul_say(place)                                          # 음성은 소리 나는 대로
    if len(out.split()) == len(place.split()):                            # 순서를 바꿔 써도 (Subi-myeon, Uljin-gun)
        for a, b in zip(out.split(), place.split()): SAY[a] = hangul_say(b)
    return out

# 한글 → 영어 목소리가 제대로 읽는 철자 (Daechi 를 "데이치"로 읽는 문제)
_CHO = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h"]
_JUNG_OPEN = ["ah", "eh", "yah", "yeh", "uh", "eh", "yuh", "yeh", "oh", "wah", "weh", "weh", "yoh", "oo", "wuh", "weh", "wee", "yoo", "uh", "ee", "ee"]
_JUNG_SHUT = ["ah", "eh", "yah", "yeh", "u", "eh", "yu", "yeh", "o", "wah", "weh", "weh", "yoh", "oo", "wo", "weh", "wee", "yoo", "u", "ee", "i"]
_JONG = ["", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l", "l", "p", "l", "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t", "p", "t"]
_SINO = "il ee sahm sah oh yook chil pahl goo".split()
SAY = {}
_LIAISON = {1: 0, 4: 2, 7: 3, 8: 5, 16: 6, 17: 7, 19: 9, 22: 12, 23: 14, 25: 16, 26: 17, 27: 11}   # 받침 → 다음 첫소리 (관악 → 과낙)
def hangul_say(text):
    syl = [list(divmod(ord(ch) - 0xAC00, 588)) if 0 <= ord(ch) - 0xAC00 < 11172 else ch for ch in text]
    syl = [[x[0], x[1] // 28, x[1] % 28] if isinstance(x, list) else x for x in syl]
    for k in range(len(syl) - 1):
        a, b = syl[k], syl[k + 1]
        if isinstance(a, list) and isinstance(b, list) and b[0] == 11 and a[2] in _LIAISON:
            b[0] = _LIAISON[a[2]]; a[2] = 0
        elif isinstance(a, list) and isinstance(b, list) and b[0] == 5 and a[2] in (4, 8):
            a[2] = 8; b.append("l")                     # 신림 → 실림 shil-lim
    parts, cur = [], ""
    for x in syl:
        if isinstance(x, list):
            cho, jung, jong = x[:3]
            v = (_JUNG_SHUT if jong else _JUNG_OPEN)[jung]
            if cho == 11 and jung == 19: v = "wee"                         # 의성 → wee-sung
            if cho == 9 and v.startswith(("ee", "i", "y", "wee")): sy = "sh" + v.lstrip("y") + _JONG[jong]      # 시·신 → shee·shin
            else: sy = ("l" if len(x) > 3 else _CHO[cho]) + v + _JONG[jong]
            cur += ("-" if cur else "") + sy
        elif x.isdigit():
            cur += (" " if cur else "") + _SINO[int(x) - 1]
        else:
            if cur: parts.append(cur); cur = ""
            parts.append(x)
    if cur: parts.append(cur)
    out = "".join(parts)
    return out[:1].upper() + out[1:]

def episode(ep):
    ds, reg = ep["dataset"], ep.get("region", "south")
    suf = "" if ds == "cvs" else "_" + ds
    sj = json.load(open(ROOT / "out" / f"sets{suf}.json", encoding="utf-8"))
    S, rs_grid = sj["sets"]["all"], sj["r"]
    res = S["results"][reg]; rs = res["r"]
    cov = S["cov"][reg]
    inv = lambda p: float(next((rs_grid[i] for i, c in enumerate(cov) if c >= p), rs))
    r50, r90 = inv(0.5), inv(0.9)
    toks = res["place"].split()
    rom = romanize(" ".join(toks[1:])) if len(toks) > 1 else romanize(res["place"])
    parts = rom.split()
    where = ", ".join(reversed(parts)) if len(parts) <= 3 else rom          # Subi-myeon, Uljin-gun
    dmz = res.get("dmz") or (res["kind"] == "coast" and res["lat"] > 37.85)
    f = lambda x: f"{x:.1f}" if x >= 1 else f"{x:.2f}"
    area = ep.get("area", "the country")
    n = ep.get("n") or S["n"]
    v = {"n": f"{n:,}", "r50": f(r50), "r90": f(r90), "rs": f"{rs:.1f}", "rs2": f"{rs:.2f}", "where": where, "area": area,
         "walk": round(rs / 4.5 * 60)}                                 # 걸어서 몇 분 (시속 4.5 km)
    say_where = f"in {where}" + (", right at the edge of the DMZ" if dmz else "")
    if ep.get("type") == "rank": return rank_episode(ep)
    if ep.get("type") == "tour": return tour_episode(ep)
    lines = [
        {"say": ep["l1"].format(**v), "cap": ep.get("c1", ep["l1"]).format(**v)},
        {"say": "Draw a circle around every one, and let them grow.", "cap": "Draw a circle around every one. Let them grow."},
        {"say": f"At {v['r50']} kilometers, half of {area} is covered.", "cap": f"At {v['r50']} km, half of {area} is covered."},
        {"say": f"At {v['r90']} kilometers, ninety percent.", "cap": f"At {v['r90']} km, 90%."},
        {"say": f"The very last spot is {say_where}.", "cap": f"The very last spot: {where}" + (", at the edge of the DMZ." if dmz else ".")},
        {"say": f"{v['rs']} kilometers from the nearest {ep['thing']}.", "cap": f"{v['rs']} km from the nearest {ep['thing']}."},
        {"say": ep["close"].format(**v), "cap": ep.get("close_cap", ep["close"]).format(**v)},
    ]
    radii = [max(0.05, r50 * 0.12), r50 * 0.35, r50, r90, min(rs * 0.9, r90 * 1.7), rs, rs, rs, rs]
    fly = 4
    if ep.get("l2"):                                                    # 첫 문장 뒤에 한 문장 더 (예: 제주에 호텔이 가장 많다)
        lines.insert(1, {"say": ep["l2"].format(**v), "cap": ep.get("c2", ep["l2"]).format(**v)})
        radii.insert(1, radii[0] * 1.4); fly = 5
    for x in ep.get("story", []):                                       # 정답 뒤 동네 이야기 → 마무리
        lines.insert(len(lines) - 1, {"say": x["say"].format(**v), "cap": x.get("cap", x["say"]).format(**v)}); radii.insert(len(radii) - 2, rs)
    look = {"theme": ep.get("theme", "dark"), "voice": ep.get("voice"), "lead": 1.75 if ep.get("cover") else None,
            "cover": [x.format(**v) for x in ep["cover"]] if ep.get("cover") else None}
    base_cam = None
    if ep.get("bbox"):                                                  # 고정 시점 (서울편)
        lo0, la0, lo1, la1 = ep["bbox"]; kmx, kmy = 111.320 * 0.8090169943749475, 110.95
        x0, x1 = (lo0 - 124.55) * kmx, (lo1 - 124.55) * kmx; y0, y1 = (38.68 - la1) * kmy, (38.68 - la0) * kmy
        s = min(W / ((x1 - x0) * 1.08), 420 / (y1 - y0))
        base_cam = {"s": s, "cx": (x0 + x1) / 2, "cy": (y0 + y1) / 2 + (480 - 470) / s}
    name = ep["id"]
    mp4 = fly_story(name, ROOT / "out" / f"mcfarthest-kr{suf}.html", res, lines, radii, ep["eye"].format(**v), ep["title"],
                    ep.get("cov_text") or f"of the land has a {ep['thing']} this close", [f"{rs:.2f} km", ep["end1"].format(**v), (where + (" · at the edge of the DMZ" if dmz else ""))],
                    fly=fly, base_cam=base_cam, region=reg, look=look)
    cap = ep["caption"].format(**v, half=f(r50)) + "\n\nInteractive map in 7 languages: desika.github.io/mcfarthest-kr\n\n" + " ".join(ep["tags"])
    (OUT / f"{name}_caption.txt").write_text(cap, encoding="utf-8")
    return mp4

def rank_episode(ep):
    """한국 ○○은 이런 곳 → ○○가 가장 많은 동네로 날아감 → 1~5위 → 마무리.
    ep["acts"]: 문장마다 nat(전국) · fly(1위 동네로) · rank(목록 펼침) · stay"""
    ds = ep["dataset"]; suf = "_" + ds
    RK = json.load(open(ROOT / "out" / "rank_stats.json", encoding="utf-8"))[ep.get("rank_key", ds)]
    top = RK[ep.get("level", "dong")][:5]
    SHORT = {"서울특별시": "Seoul", "부산광역시": "Busan", "대구광역시": "Daegu", "인천광역시": "Incheon", "광주광역시": "Gwangju", "대전광역시": "Daejeon", "울산광역시": "Ulsan"}
    rows = []
    for x in top:
        sgg = romanize(x["sgg"]); dong = romanize(x["dong"]) if x.get("dong") else sgg
        city = SHORT.get(x["sido"], "")
        rows.append({"a": dong, "b": (sgg + (", " + city if city else "")) if x.get("dong") else city, "n": x["n"]})
    sj = json.load(open(ROOT / "out" / f"sets{suf}.json", encoding="utf-8")); S = sj["sets"]["all"]
    res = S["results"]["south"]; rs = res["r"]
    v = {"n": f"{RK['n']:,}", "rs": f"{rs:.1f}", "top": rows[0]["a"], "top_b": rows[0]["b"], "top_n": f"{rows[0]['n']:,}",
         "second": rows[1]["a"], "second_b": rows[1]["b"], "third": rows[2]["a"], "third_b": rows[2]["b"],
         "sgg1": romanize(RK["sgg"][0]["sgg"]), "sgg1_n": f"{RK['sgg'][0]['n']:,}"}
    lines = [{"say": l["say"].format(**v), "cap": l.get("cap", l["say"]).format(**v)} for l in ep["lines"]]
    acts = ep["acts"]; assert len(acts) == len(lines)
    look = {"theme": ep.get("theme", "dark"), "voice": ep.get("voice"), "lead": 1.75 if ep.get("cover") else None,
            "cover": [x.format(**v) for x in ep["cover"]] if ep.get("cover") else None}
    work = Path(tempfile.mkdtemp(prefix="reel_"))
    clips, total, audio = narrate(lines, work, look["voice"], look["lead"])
    T = [c["t0"] for c in clips] + [clips[-1]["t1"], total]
    kmx, kmy = 111.320 * 0.8090169943749475, 110.95
    lo0, la0, lo1, la1 = top[0]["bbox"]
    x0, x1 = (lo0 - 124.55) * kmx, (lo1 - 124.55) * kmx; y0, y1 = (38.68 - la1) * kmy, (38.68 - la0) * kmy
    sd = max(6.0, min(220.0, 230 / (x1 - x0 + 0.5), 300 / (y1 - y0 + 0.5)))
    dist = {"s": sd, "cx": (x0 + x1) / 2 - (395 - 270) / sd, "cy": (y0 + y1) / 2 - (470 - 480) / sd}   # 1위 동네를 화면 오른쪽 가운데
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome"); pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.goto((ROOT / "out" / f"mcfarthest-kr{suf}.html").as_uri() + "#en"); pg.add_style_tag(content=REEL_CSS); pg.evaluate("() => window.dispatchEvent(new Event('resize'))")
        pg.wait_for_function("() => window.MF && MF.ready()", timeout=60000)
        nat = pg.evaluate("r => MF.camera(r)", 30); br.close()
    nat["cy"] += 40 / nat["s"]                                            # 전국 지도를 조금 아래로 (제목 자리)
    i_fly = acts.index("fly"); i_rank = acts.index("rank") if "rank" in acts else i_fly + 1
    r_nat0, r_nat1, r_loc = ep.get("r_nat", [0.6, 2.2]) + [None]
    r_loc = ep.get("r_local", 0.12)
    def at(t):
        k = next((i for i in range(len(T) - 1) if T[i] <= t < T[i + 1]), len(T) - 2)
        if t < T[i_fly]:
            u = ease(t / T[i_fly]); r = lerp_log(r_nat0, r_nat1, u); cam = nat
        else:
            u2 = ease((t - T[i_fly]) / max(1e-6, T[i_fly + 1] - T[i_fly]))
            cam = {"s": lerp_log(nat["s"], dist["s"], u2), "cx": nat["cx"] + (dist["cx"] - nat["cx"]) * u2, "cy": nat["cy"] + (dist["cy"] - nat["cy"]) * u2}
            r = lerp_log(r_nat1, r_loc, u2)
        rank_op = 0.0 if t < T[i_fly] + 0.6 else min(1.0, (t - T[i_fly] - 0.6) / 0.4)
        rank_n = 1 if t < T[i_rank] else (3 if t < (T[i_rank] + T[i_rank + 1]) / 2 else 5)
        cap = next((c["cap"] for c in clips if c["t0"] - 0.15 <= t <= c["t1"] + GAP * 0.8), "")
        end = ease((t - (total - TAIL + 0.4)) / 0.8) if t > total - TAIL + 0.4 else 0
        return {"r": r, "cam": cam, "keys": 0, "eye": ep["eye"].format(**v), "showRad": False, "title": ep["title"],
                "cap": cap, "capTop": 690, "end": end, "endText": [x.format(**v) for x in ep["end"]],
                "rank": rows, "rankN": rank_n, "rankOp": round(rank_op, 3), **cover_state(t, look)}
    mp4 = capture(ep["id"], at, total, audio, work, ROOT / "out" / f"mcfarthest-kr{suf}.html")
    cap = ep["caption"].format(**v) + "\n\nInteractive map in 7 languages: desika.github.io/mcfarthest-kr\n\n" + " ".join(ep["tags"])
    (OUT / f"{ep['id']}_caption.txt").write_text(cap, encoding="utf-8")
    return mp4

def tour_episode(ep):
    """전국 → stops 를 차례로 날아가며 들르고, 들를 때마다 순위판에 한 줄씩 쌓는다.
    ep["acts"]: 문장마다 nat · stop0 · stop1 … · stay"""
    import csv, statistics
    ds = ep["dataset"]; suf = "_" + ds
    rows_all = list(csv.DictReader(open(ROOT / "data" / f"chain_{ds}.csv", encoding="utf-8")))
    kmx, kmy = 111.320 * 0.8090169943749475, 110.95
    stops = []
    for st_ in ep["stops"]:
        rr = [r for r in rows_all if r["sido"].startswith(st_["sido"]) and r["sigungu"] == st_["sgg"] and (not st_.get("dong") or r["dong"] == st_["dong"])]
        lo = sorted(float(r["lon"]) for r in rr); la = sorted(float(r["lat"]) for r in rr)
        q = lambda a, f: a[min(len(a) - 1, max(0, int(len(a) * f)))]
        lo0, lo1, la0, la1 = q(lo, .05), q(lo, .95), q(la, .05), q(la, .95)
        x0, x1 = (lo0 - 124.55) * kmx, (lo1 - 124.55) * kmx; y0, y1 = (38.68 - la1) * kmy, (38.68 - la0) * kmy
        sd = max(6.0, min(200.0, 210 / (x1 - x0 + 0.6), 260 / (y1 - y0 + 0.6)))
        name = romanize(st_["dong"]) if st_.get("dong") else romanize(st_["sgg"])
        stops.append({"cam": {"s": sd, "cx": (x0 + x1) / 2 - (395 - 270) / sd, "cy": (y0 + y1) / 2 - (470 - 480) / sd},
                      "row": {"a": name, "b": st_["label"], "n": len(rr)}, "n": len(rr)})
    v = {"n": f"{len(rows_all):,}"}
    for i, x in enumerate(stops): v[f"s{i}"] = x["row"]["a"]; v[f"s{i}_n"] = f"{x['n']:,}"; v[f"s{i}_b"] = x["row"]["b"]
    lines = [{"say": l["say"].format(**v), "cap": l.get("cap", l["say"]).format(**v)} for l in ep["lines"]]
    acts = ep["acts"]; assert len(acts) == len(lines)
    look = {"theme": ep.get("theme", "dark"), "voice": ep.get("voice"), "lead": 1.75 if ep.get("cover") else None,
            "cover": [x.format(**v) for x in ep["cover"]] if ep.get("cover") else None}
    work = Path(tempfile.mkdtemp(prefix="reel_"))
    clips, total, audio = narrate(lines, work, look["voice"], look["lead"])
    T = [c["t0"] for c in clips] + [clips[-1]["t1"], total]
    page = ROOT / "out" / f"mcfarthest-kr{suf}.html"
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome"); pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.goto(page.as_uri() + "#en"); pg.add_style_tag(content=REEL_CSS); pg.evaluate("() => window.dispatchEvent(new Event('resize'))")
        pg.wait_for_function("() => window.MF && MF.ready()", timeout=60000)
        nat = pg.evaluate("r => MF.camera(r)", 30); br.close()
    nat["cy"] += 40 / nat["s"]
    # 문장마다 출발·도착 시점
    seq = []                                                          # (시작시각, 출발 cam, 도착 cam, 반지름 출발, 도착)
    cur, r_cur = nat, ep.get("r_nat", [0.4, 1.6])[0]
    r_nat1, r_loc = ep.get("r_nat", [0.4, 1.6])[1], ep.get("r_local", 0.06)
    visited = []
    for i, a in enumerate(acts):
        if a.startswith("stop"):
            k = int(a[4:]); dst = stops[k]["cam"]; seq.append((T[i], cur, dst, r_cur, r_loc)); cur, r_cur = dst, r_loc; visited.append((T[i], k))
        elif a == "nat":
            seq.append((T[i], cur, nat, r_cur, r_nat1 if i == acts.index("nat") or True else r_cur)); cur, r_cur = nat, r_nat1
    def at(t):
        cam, r = nat, ep.get("r_nat", [0.4, 1.6])[0]
        for (t0, a, b, ra, rb) in seq:
            if t < t0: break
            dur = 1.5 if a is not b else 1.0
            u = ease((t - t0) / dur) if a is not b else ease((t - t0) / max(1e-6, (T[1] if len(T) > 1 else 3) - T[0]))
            cam = {"s": lerp_log(a["s"], b["s"], u), "cx": a["cx"] + (b["cx"] - a["cx"]) * u, "cy": a["cy"] + (b["cy"] - a["cy"]) * u}
            r = lerp_log(ra, rb, u)
        shown = [stops[k]["row"] for (t0, k) in visited if t >= t0 + 0.9]
        cap = next((c["cap"] for c in clips if c["t0"] - 0.15 <= t <= c["t1"] + GAP * 0.8), "")
        end = ease((t - (total - TAIL + 0.4)) / 0.8) if t > total - TAIL + 0.4 else 0
        return {"r": r, "cam": cam, "keys": 0, "eye": ep["eye"].format(**v), "showRad": False, "title": ep["title"],
                "cap": cap, "capTop": 690, "end": end, "endText": [x.format(**v) for x in ep["end"]],
                "rank": shown or None, "rankN": len(shown), "rankOp": 1.0 if shown else 0.0, **cover_state(t, look)}
    mp4 = capture(ep["id"], at, total, audio, work, page)
    cap = ep["caption"].format(**v) + "\n\nInteractive map in 7 languages: desika.github.io/mcfarthest-kr\n\n" + " ".join(ep["tags"])
    (OUT / f"{ep['id']}_caption.txt").write_text(cap, encoding="utf-8")
    return mp4

# ── 편: 담배 살 수 있는 곳에서 가장 먼 곳 ──
def tobacco():
    st = json.load(open(ROOT / "out" / "sets_tobacco.json", encoding="utf-8"))["sets"]["all"]
    res = st["results"]["south"]; rs = res["r"]
    return fly_story("tobacco", ROOT / "out" / "mcfarthest-kr_tobacco.html", res, lines=[
        {"say": "In South Korea, a hundred and twenty-one thousand places sell cigarettes.", "cap": "121,260 places sell cigarettes in South Korea."},
        {"say": "That's more than twice the number of convenience stores.", "cap": "More than twice the number of convenience stores."},
        {"say": "Draw a circle around every one, and let them grow.", "cap": "Draw a circle around every one. Let them grow."},
        {"say": "At three kilometers, eighty-five percent of the land is covered.", "cap": "At 3 km, 85% of the land is covered."},
        {"say": "At five kilometers, ninety-eight percent.", "cap": "At 5 km, 98%."},
        {"say": "The very last spot is in Hwacheon, right at the edge of the DMZ.", "cap": "The very last spot: Hwacheon, at the edge of the DMZ."},
        {"say": "Ten point one kilometers. Half the distance of the convenience store answer.", "cap": "10.1 km. Half the convenience store answer."},
        {"say": "In Korea, you can't get more than ten kilometers from a pack of cigarettes.", "cap": "You can't get more than 10 km from a pack of cigarettes."},
    ], radii=[0.1, 0.22, 0.5, 1.6, 3.0, 5.0, rs, rs, rs, rs], eye="SOUTH KOREA · 121,260 TOBACCO RETAILERS",
       title="How far can you get from a pack of <b>cigarettes</b>?", cov_text="of the land has a seller this close",
       end_text=[f"{rs:.2f} km", "The farthest you can get from a place that sells cigarettes in South Korea", "Hwacheon, Gangwon · at the edge of the DMZ"])

# ── 편: 브랜드 대결 (나쁜 쪽 → 좋은 쪽으로 긴장을 쌓음) ──
def brands():
    R = {b: SETS[b]["results"]["south"]["r"] for b in ("e24", "se", "gs", "cu", "all")}
    name = {"e24": "emart24", "se": "7-Eleven", "gs": "GS25", "cu": "CU", "all": "ALL STORES"}
    say = lambda x: f"{x:.1f}".replace(".", " point ")
    lines = [
        {"say": "Korea's big four convenience store chains. Which one covers the country best?", "cap": "Korea's big four chains. Which one covers the country best?", "b": "all", "r0": 0.5, "r1": 3.0},
        {"say": f"Keep only emart24, and the farthest spot is {round(R['e24'])} kilometers away.", "cap": f"Only emart24: {R['e24']:.1f} km to the farthest spot.", "b": "e24"},
        {"say": f"Only 7-Eleven: {say(R['se'])}.", "cap": f"Only 7-Eleven: {R['se']:.1f} km.", "b": "se"},
        {"say": f"Only GS25: {say(R['gs'])}.", "cap": f"Only GS25: {R['gs']:.1f} km.", "b": "gs"},
        {"say": f"And CU wins, at {say(R['cu'])}.", "cap": f"CU wins: {R['cu']:.1f} km.", "b": "cu"},
        {"say": "Put them all together, and you can never get more than twenty kilometers away.", "cap": "All together: never more than 20 km away.", "b": "all"},
        {"say": "Which one is closest to you?", "cap": "Which one is closest to you?", "b": "all", "hold": True},
    ]
    work = Path(tempfile.mkdtemp(prefix="reel_"))
    clips, total, audio = narrate(lines, work)
    def at(t):
        c = next((c for c in clips if t < c["t1"] + GAP), clips[-1])
        u = ease((t - c["t0"]) / max(1e-6, c["t1"] - c["t0"]))
        b = c["b"]; rs = R[b]
        r0, r1 = c.get("r0", rs * 0.35), c.get("r1", rs)
        r = rs if c.get("hold") else lerp_log(r0, r1, u)
        cap = c["cap"] if c["t0"] - 0.15 <= t <= c["t1"] + GAP * 0.8 else ""
        end = ease((t - (total - TAIL + 0.4)) / 0.8) if t > total - TAIL + 0.4 else 0
        return {"r": r, "cam": None, "brand": b, "eye": "SOUTH KOREA · FARTHEST POINT BY CHAIN", "showRad": True,
                "title": "Which chain covers <b>Korea</b> best?", "tag": name[b], "cap": cap, "end": end,
                "endText": ["CU", "covers Korea best of the big four", f"CU {R['cu']:.1f} km · GS25 {R['gs']:.1f} · 7-Eleven {R['se']:.1f} · emart24 {R['e24']:.1f}"]}
    return capture("brands", at, total, audio, work)

if __name__ == "__main__":
    EPS = {e["id"]: e for e in json.load(open(ROOT / "tools" / "episodes.json", encoding="utf-8"))}
    for name in sys.argv[1:] or ["farthest"]:
        episode(EPS[name]) if name in EPS else globals()[name]()
