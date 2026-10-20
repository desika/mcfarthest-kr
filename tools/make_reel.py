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
async def _tts(text, path):
    await edge_tts.Communicate(text, VOICE, rate="-4%").save(str(path))
def duration(path):
    r = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)
def narrate(lines, work):
    clips, t = [], LEAD
    for i, ln in enumerate(lines):
        p = work / f"v{i:02d}.mp3"; asyncio.run(_tts(ln["say"], p)); d = duration(p)
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
"""
REEL_HTML = """<div id="reel"><div class="band-t"></div><div class="band-b"></div>
<div class="eyebrow" id="r-eye"></div><div class="title" id="r-title"></div>
<div class="rad" id="r-rad"></div><div class="cov" id="r-cov"></div><div class="tag" id="r-tag"></div>
<svg id="r-svg" viewBox="0 0 540 960"></svg><div class="cap" id="r-cap"></div>
<div class="end" id="r-end"><div class="big" id="e-big"></div><div class="t1" id="e-t1"></div><div class="t2" id="e-t2"></div><div class="url">desika.github.io/mcfarthest-kr</div></div></div>"""
FRAME_JS = """(p) => {
  const st = MF.st;
  if (p.brand && st.b !== p.brand) MF.setBrand(p.brand);
  st.r = p.r; st.cam = p.cam; MF.render();
  const $ = id => document.getElementById(id);
  $("r-eye").textContent = p.eye; $("r-title").innerHTML = p.title;
  const r = p.r, rs = r < 1 ? r.toFixed(2) : r < 10 ? r.toFixed(1) : r.toFixed(1);
  $("r-rad").innerHTML = p.showRad ? `r = ${rs}<small>km</small>` : "";
  const c = Math.min(100, MF.cov(r) * 100);
  $("r-cov").innerHTML = p.showRad ? `<b>${c >= 99.95 && r < MF.res().r ? "99.9" : c.toFixed(1)}%</b> ${p.covText || "of the land has a store this close"}` : "";
  $("r-tag").textContent = p.tag || "";
  $("r-cap").textContent = p.cap || "";
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
  const e = $("r-end"); e.style.opacity = p.end || 0;
  if (p.endText) { $("e-big").textContent = p.endText[0]; $("e-t1").textContent = p.endText[1]; $("e-t2").textContent = p.endText[2]; }
}"""

def ease(t): return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))
def lerp_log(a, b, t): return math.exp(math.log(a) + (math.log(b) - math.log(a)) * t)

def capture(name, frames_fn, total, audio, work, page=PAGE):
    frames = work / "f"; frames.mkdir()
    n = int(total * FPS)
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome", args=["--hide-scrollbars"])
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.goto(page.as_uri() + "#en")
        pg.add_style_tag(content=REEL_CSS)
        pg.evaluate("h => document.body.insertAdjacentHTML('beforeend', h)", REEL_HTML)
        pg.evaluate("() => window.dispatchEvent(new Event('resize'))")
        pg.wait_for_function("() => window.MF && MF.ready()", timeout=60000)
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

def fly_story(name, page, res, lines, radii, eye, title, cov_text, end_text):
    """원이 자라다 끝에서 두 번째 문장에서 정답 지점으로 날아가는 이야기"""
    rs = res["r"]
    work = Path(tempfile.mkdtemp(prefix="reel_"))
    clips, total, audio = narrate(lines, work)
    T = [c["t0"] for c in clips] + [clips[-1]["t1"], total]
    # 목표 시점: 울진 수비면을 화면 가운데, 세로로 3.4 r*
    kmx, kmy = 111.320 * 0.8090169943749475, 110.95
    tx, ty = (res["lon"] - 124.55) * kmx, (38.68 - res["lat"]) * kmy
    s_t = W / (rs * 5.4)                                               # 세 원이 다 들어오는 축척
    target = {"s": s_t, "cx": tx, "cy": ty + (480 - 505) / s_t}      # 정답 점을 글자와 자막 사이에
    nat = {"s": None}
    def at(t):
        k = max(0, min(len(T) - 2, next((i for i in range(len(T) - 1) if T[i] <= t < T[i + 1]), len(T) - 2)))
        u = (t - T[k]) / max(1e-6, T[k + 1] - T[k])
        r = lerp_log(radii[k], radii[k + 1], ease(u)) if k < len(radii) - 1 else rs
        if t < T[0]: r = radii[0]
        cap = next((c["cap"] for c in clips if c["t0"] - 0.15 <= t <= c["t1"] + GAP * 0.8), "")
        cam, keys = None, 0
        if t >= T[5]:                                                   # "마지막 한 점" 문장부터 울진으로
            u2 = ease((t - T[5]) / (T[6] - T[5]))
            a = nat.get("cam") or {"s": 0.0, "cx": tx, "cy": ty}
            cam = {"s": lerp_log(a["s"], target["s"], u2), "cx": a["cx"] + (target["cx"] - a["cx"]) * u2, "cy": a["cy"] + (target["cy"] - a["cy"]) * u2}
            keys = round(u2, 3)
        end = ease((t - (total - TAIL + 0.4)) / 0.8) if t > total - TAIL + 0.4 else 0
        return {"r": r, "cam": cam, "keys": keys, "eye": eye, "showRad": True, "covText": cov_text,
                "title": title, "cap": cap, "end": end, "endText": end_text}
    # 확대 시작 시점의 전국 카메라를 페이지에서 받아 둔다
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome"); pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.goto(page.as_uri() + "#en"); pg.add_style_tag(content=REEL_CSS); pg.evaluate("() => window.dispatchEvent(new Event('resize'))")
        pg.wait_for_function("() => window.MF && MF.ready()", timeout=60000)
        nat["cam"] = pg.evaluate("r => MF.camera(r)", radii[5]); br.close()
    return capture(name, at, total, audio, work, page)

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
    for name in sys.argv[1:] or ["farthest"]:
        globals()[name]()
