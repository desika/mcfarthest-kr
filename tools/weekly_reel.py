"""릴스 자동 게시 — PC 를 켜면(로그온) 그리고 매일 낮에 한 번 실행 (PC 켜는 날 1편)

  python tools/weekly_reel.py            # 할 일 있으면 함
  python tools/weekly_reel.py --dry      # 만들기만, 올리지 않음
  python tools/weekly_reel.py --force    # 오늘 이미 올렸어도 다음 편
  python tools/weekly_reel.py --force --ready   # 이미 만들어 둔 영상(사람이 확인한 것)을 그대로 올림

규칙
  - 오늘(KST) 아직 안 올렸을 때만 다음 편을 올린다 (PC 켜는 날 하루 1편)
  - 한국시각 09~22시에만 올린다. 밖이면 다음 실행 때
  - 대기열 tools/episodes.json 에서 아직 안 올린 첫 편 → 영상 → 서버 공개 경로 → post_reel.sh
  - 기록 out/reels/state.json · 로그 out/reels/weekly.log
  - 성공·실패 모두 텔레그램 알림 (서버 notify.sh). 조용히 지나가는 실패 경로 없음
"""
import datetime as dt, json, os, subprocess, sys, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REELS = ROOT / "out" / "reels"; REELS.mkdir(parents=True, exist_ok=True)
STATE = REELS / "state.json"; LOG = REELS / "weekly.log"; LOCK = REELS / "weekly.lock"
PY = sys.executable
ENV = dict(l.split("=", 1) for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if "=" in l and not l.startswith("#"))
KEY, HOST = ENV["REEL_SSH_KEY"].strip(), ENV["REEL_SSH_HOST"].strip()     # 서버 주소·키 위치는 .env (공개 저장소에 두지 않음)
SSH = ["ssh", "-i", KEY, "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", HOST]
SCP = ["scp", "-q", "-i", KEY, "-o", "ConnectTimeout=20", "-o", "BatchMode=yes"]
PUB_DIR, PUB_URL = "/home/ubuntu/abc-news-learner/cards/reels", "https://learner.rabotakorea.online/cards/reels"
KST = dt.timezone(dt.timedelta(hours=9))
now = dt.datetime.now(KST)

def log(*a):
    line = f"[{dt.datetime.now(KST):%Y-%m-%d %H:%M:%S}] " + " ".join(str(x) for x in a)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")
    try: print(line, flush=True)
    except Exception: pass

def notify(msg):
    try:
        subprocess.run(SSH + [f"/home/ubuntu/abc-news-learner/notify.sh {json.dumps('[편의점 릴스] ' + msg)}"], capture_output=True, timeout=60)
    except Exception as e:
        log("알림 실패", e)

def run(cmd, env=None, timeout=3600):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=timeout)
    if r.returncode != 0: raise RuntimeError(f"{' '.join(map(str, cmd[:3]))} 실패\n{(r.stdout + r.stderr)[-1500:]}")
    return r.stdout

def main():
    args = set(sys.argv[1:])
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"posted": []}
    if state["posted"] and "--force" not in args:
        last = dt.datetime.fromisoformat(state["posted"][-1]["at"])
        if last.astimezone(KST).date() >= now.date():
            log(f"할 일 없음 — 오늘 이미 올림 ({last:%m-%d %H:%M}), 다음은 내일"); return
    if not (9 <= now.hour < 22) and "--force" not in args and "--dry" not in args:
        log(f"게시 시간 아님 ({now:%H:%M} KST) — 09~22시에 다시"); return
    eps = json.loads((ROOT / "tools" / "episodes.json").read_text(encoding="utf-8"))
    done = {p["id"] for p in state["posted"]}
    todo = [e for e in eps if e["id"] not in done]
    if not todo:
        log("대기열이 비었음"); notify("대기열의 편을 다 올렸습니다. 새 편을 넣어 주세요"); return
    ep = todo[0]; name = ep["id"]
    log("다음 편", name)
    # 데이터셋 페이지가 없으면 만든다
    suf = "" if ep["dataset"] == "cvs" else "_" + ep["dataset"]
    if not (ROOT / "out" / f"mcfarthest-kr{suf}.html").exists() or not (ROOT / "out" / f"sets{suf}.json").exists():
        env = {**os.environ, "MF_DATASET": ep["dataset"]}
        for s in ("src/compute_sets.py", "src/build_data.py", "src/build_page.py"): run([PY, "-I", s], env=env)
    mp4, cap, cov = REELS / f"{name}.mp4", REELS / f"{name}_caption.txt", REELS / f"{name}_cover.jpg"
    if "--ready" not in args or not mp4.exists(): run([PY, "-I", "tools/make_reel.py", name], timeout=7200)
    if not mp4.exists() or mp4.stat().st_size < 1_000_000: raise RuntimeError("영상이 만들어지지 않음")
    log("영상", mp4.name, round(mp4.stat().st_size / 1e6, 1), "MB")
    if "--dry" in args: log("--dry: 올리지 않음"); return
    run(SCP + [str(mp4), f"{HOST}:{PUB_DIR}/"]); run(SCP + [str(cap), f"{HOST}:/home/ubuntu/mcfarthest-kr/reels/"])
    cover = ""
    if cov.exists(): run(SCP + [str(cov), f"{HOST}:{PUB_DIR}/"]); cover = f"{PUB_URL}/{cov.name}"     # 표지 = 첫 장면
    else: log("표지 없음 — 인스타 기본 표지로")
    out = run(SSH + [f"cd /home/ubuntu/mcfarthest-kr/reels && bash post_reel.sh {PUB_URL}/{mp4.name} {cap.name} {cover}"], timeout=900)
    ok = [l for l in out.splitlines() if l.startswith("OK ")]
    if not ok: raise RuntimeError("게시 결과 없음\n" + out[-800:])
    _, mid, link = ok[-1].split(" ", 2)
    state["posted"].append({"id": name, "at": now.isoformat(timespec="seconds"), "media_id": mid, "link": link})
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    log("게시 완료", name, link)        # 성공 알림은 post_reel.sh 가 보냄

if __name__ == "__main__":
    if LOCK.exists() and (dt.datetime.now().timestamp() - LOCK.stat().st_mtime) < 3 * 3600:
        log("이미 실행 중 — 건너뜀"); sys.exit(0)
    LOCK.write_text(str(os.getpid()))
    try:
        main()
    except Exception as e:
        log("실패", e, traceback.format_exc()[-1500:])
        notify(f"자동 게시 실패: {str(e)[:300]}")
        sys.exit(1)
    finally:
        LOCK.unlink(missing_ok=True)
