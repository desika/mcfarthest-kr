#!/usr/bin/env bash
# 인스타 릴스 올리기 — 서버(nfc-amd-server)에서 실행
#   bash post_reel.sh <영상 공개 URL> <본문 파일>
# 토큰·계정은 abc-news-learner 의 .env (IG_USER_ID, FB_PAGE_TOKEN) 를 그대로 쓴다.
#   ① 컨테이너 (media_type=REELS, video_url)  ② 메타가 영상을 다 받을 때까지 대기(FINISHED)  ③ 발행
# 인스타 게시물은 API 로 지울 수 없다. 사람이 확인한 영상만 넣을 것.
set -u
VIDEO_URL="${1:?영상 URL}"; CAPTION_FILE="${2:?본문 파일}"
ENV=/home/ubuntu/abc-news-learner/.env
set -a; . "$ENV"; set +a
API="https://graph.facebook.com/v21.0"
notify() { [ -x /home/ubuntu/abc-news-learner/notify.sh ] && /home/ubuntu/abc-news-learner/notify.sh "$1" >/dev/null 2>&1 || true; }
fail() { echo "FAIL: $1"; notify "릴스 게시 실패: $1"; exit 1; }

[ -n "${IG_USER_ID:-}" ] && [ -n "${FB_PAGE_TOKEN:-}" ] || fail ".env 에 IG_USER_ID / FB_PAGE_TOKEN 없음"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -I "$VIDEO_URL"); [ "$CODE" = "200" ] || fail "영상 URL 접근 불가 ($CODE)"
CAPTION=$(cat "$CAPTION_FILE")

RESP=$(curl -sS -X POST "$API/${IG_USER_ID}/media" \
  --data-urlencode "media_type=REELS" --data-urlencode "video_url=${VIDEO_URL}" \
  --data-urlencode "caption=${CAPTION}" --data-urlencode "share_to_feed=true" \
  --data-urlencode "access_token=${FB_PAGE_TOKEN}")
CID=$(echo "$RESP" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("id") or "")')
[ -n "$CID" ] || fail "컨테이너 생성 — $RESP"
echo "컨테이너 $CID"

for i in $(seq 1 40); do                      # 최대 약 7분
  ST=$(curl -sS -G "$API/$CID" --data-urlencode "fields=status_code,status" --data-urlencode "access_token=${FB_PAGE_TOKEN}" \
       | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("status_code","?"), d.get("status",""))')
  echo "  [$i] $ST"
  case "$ST" in FINISHED*) break ;; ERROR*|EXPIRED*) fail "영상 처리 — $ST" ;; esac
  sleep 10
done
case "$ST" in FINISHED*) ;; *) fail "영상 처리 시간 초과 — $ST" ;; esac

RESP=$(curl -sS -X POST "$API/${IG_USER_ID}/media_publish" --data-urlencode "creation_id=${CID}" --data-urlencode "access_token=${FB_PAGE_TOKEN}")
MID=$(echo "$RESP" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("id") or "")')
[ -n "$MID" ] || fail "발행 — $RESP"
LINK=$(curl -sS -G "$API/$MID" --data-urlencode "fields=permalink" --data-urlencode "access_token=${FB_PAGE_TOKEN}" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("permalink",""))')
echo "OK $MID $LINK"
notify "릴스 게시 완료: $LINK"
