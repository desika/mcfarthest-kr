' 매주 릴스 자동 게시를 창 없이 실행 (시작프로그램 폴더 + 매일 예약작업에서 부름)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "E:\26dev-1\mcfarthest-kr"
sh.Run """C:\Users\wonse\AppData\Local\Programs\Python\Python313\python.exe"" -I tools\weekly_reel.py", 0, False
