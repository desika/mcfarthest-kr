"""상호명 → 브랜드. 운영 법인 이름으로 등록된 점포도 묶는다."""
import re

SETS = [("all", "전체"), ("gs", "GS25"), ("cu", "CU"), ("se", "세븐일레븐"), ("e24", "이마트24")]

def brand(name: str) -> str:
    n = name.upper().replace(" ", "")
    if re.search(r"GS25|지에스25|지에스이십오|GS편의점|지에스편의점", n): return "gs"
    if n.startswith("CU") or "씨유" in n or "비지에프리테일" in n or "비지에프휴먼" in n: return "cu"
    if re.search(r"세븐일레븐|7-?ELEVEN|세븐-일레븐|코리아세븐", n): return "se"
    if re.search(r"이마트24|EMART24|이마트투에니포|위드미", n): return "e24"
    return "etc"
