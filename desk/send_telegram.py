import os,glob,urllib.request,urllib.parse
t=open(sorted(glob.glob('state/report-*.txt'))[-1]).read()[:4000]
d=urllib.parse.urlencode({'chat_id':os.environ['TELEGRAM_CHAT_ID'],'text':t}).encode()
urllib.request.urlopen(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",d)
print("telegram sent")
