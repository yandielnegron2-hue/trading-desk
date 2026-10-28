import json,os,html,glob
S='desk/state'
def j(p):
    try: return json.load(open(p))
    except Exception: return {}
dial=j('risk-dial/latest.json')
hist=[json.loads(l) for l in open('risk-dial/history.jsonl')] if os.path.exists('risk-dial/history.jsonl') else []
rep=open(sorted(glob.glob(S+'/report-*.txt'))[-1]).read() if glob.glob(S+'/report-*.txt') else 'no report yet'
d={k:v['dial'] for k,v in dial.get('dials',{}).items()}; g={k:v.get('green') for k,v in dial.get('inputs',{}).items()}
def card(name,sub,val,color):
    return f'<div class="card" style="border-top:3px solid {color}"><div class="t" style="color:{color}">{name}</div><div class="s">{sub}</div><div class="v">{val}</div></div>'
cards=''.join(card(k.upper(),'dial',f"{v:.2f}",'#3ee07a' if v>=0.75 else '#f5c542' if v>=0.5 else '#ff4d6d') for k,v in d.items())
cards=f'<div class="card" style="border-top:3px solid #ff5fb0"><div class="t">MOMENTUM</div><div class="s">crypto target</div><div class="v">{html.escape(str(dial.get("momentum_12_1",{}).get("allocation")))}</div></div>'+cards if False else cards
cards+=''.join(card(k.upper(),'input','GREEN' if v else 'RED','#3ee07a' if v else '#ff4d6d') for k,v in g.items())
pts=[(h.get('generated_utc','')[5:16].replace('T',' '), {k:v['dial'] for k,v in h.get('dials',{}).items()}) for h in hist]
page=f'''<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>GROKBOT DESK</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>body{{background:#0b0b10;color:#e6e6ef;font-family:ui-monospace,Menlo,monospace;margin:0;padding:16px}}
.top{{background:#ff5fb0;color:#111;padding:10px 16px;font-weight:900;font-size:22px;border-radius:8px;display:flex;justify-content:space-between}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:14px 0}}
.card{{background:#15151d;border-radius:8px;padding:10px}}.t{{font-weight:800}}.s{{font-size:11px;opacity:.6}}.v{{font-size:22px;margin-top:6px}}
.panel{{background:#15151d;border:1px solid #ff5fb0;border-radius:8px;padding:12px;margin-top:12px}}pre{{white-space:pre-wrap;font-size:12px}}</style></head><body>
<div class="top"><span>GROKBOT DESK · DRY-RUN</span><span>{html.escape(str(dial.get("generated_utc","")))}</span></div>
<div class="grid">{cards}</div>
<div class="panel"><b>DIAL HISTORY</b><canvas id=c height=90></canvas></div>
<div class="panel"><b>DESK REPORT</b><pre>{html.escape(rep)}</pre></div>
<script>const P={json.dumps(pts)};new Chart(document.getElementById('c'),{{type:'line',data:{{labels:P.map(p=>p[0]),datasets:['meme','stocks','crypto'].map((k,i)=>({{label:k,data:P.map(p=>p[1][k]),borderColor:['#ff5fb0','#3ee07a','#4da3ff'][i]}}))}},options:{{scales:{{y:{{min:0,max:1}}}}}}}});</script>
</body></html>'''
os.makedirs('site',exist_ok=True);open('site/index.html','w').write(page);print('built')
