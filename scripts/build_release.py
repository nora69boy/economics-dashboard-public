"""Reproducible v0.6 build from versioned templates and validated public numeric snapshots."""
import base64,hashlib,json,re
from html import escape
from pathlib import Path
import build_dashboard,calendar_snapshot
from macro_core import validate,validate_calendar
ROOT=Path(__file__).resolve().parents[1]
def build():
 md=(ROOT/'site/data/macro.json').read_text();cd=json.dumps(calendar_snapshot.build(),separators=(',',':'))+'\n';(ROOT/'site/data/macro-calendar.json').write_text(cd)
 macro=json.loads(md);cal=json.loads(cd);validate(macro);validate_calendar(cal);text=build_dashboard.build()
 start=text.index('// Data coverage is a measured inventory, never a fictional market reading.');end=text.index("const operations=$('operations');",start)
 text=text[:start]+'// Macro history rendered by the independent typed-data module.\n'+text[end:]
 text=text.replace("badge('SNAPSHOT / '","badge('STOCK SNAPSHOT / '")
 text=text.replace('v0.5.0','v0.6.0').replace("version:'0.5.0'","version:'0.6.0'")
 text=text.replace("const archive=$('archive');archive.append(card('v0.6.0 /", "const archive=$('archive');archive.append(card('v0.5.0 /")
 text=text.replace("['0','接続済み自動取得','リアルタイム値なし']","['6','マクロ自動取得系列','公的データ / 株価は対象外']")
 text=text.replace('自動更新なし / 追跡タグなし','マクロのみ定期取得 / 追跡タグなし')
 embedded='<pre id="macro-data" hidden>'+escape(md)+'</pre><pre id="macro-calendar-data" hidden>'+escape(cd)+'</pre>'
 fallback='<noscript><article><h2>Macro data / JavaScript disabled</h2><p>Static observations only. VIX withheld pending republication permission. Calendar and charts require JavaScript.</p><table><thead><tr><th>Series</th><th>Observation date</th><th>Raw value</th><th>Status</th></tr></thead><tbody>'
 for s in macro['series']:
  latest=s['observations'][-1] if s['observations'] else ['--','--'];fallback+='<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in [s['id'],*latest,s['status']])+'</tr>'
 fallback+='</tbody></table></article></noscript>';text=text.replace('</body>',embedded+fallback+'</body>')
 code=re.findall(r'<script[^>]*>(.*?)</script>',text,re.S)[0]+'\n'+(ROOT/'templates/macro.js').read_text()
 text=re.sub(r'<script[^>]*>.*?</script>',lambda _:'<script>'+code+'</script>',text,flags=re.S)
 script='<script>'+code+'</script>';text=text.replace(script,'').replace('</body>',script+'</body>');text=text.replace('</style>',(ROOT/'templates/macro.css').read_text()+'</style>',1)
 digest=base64.b64encode(hashlib.sha256(code.encode()).digest()).decode();text=re.sub(r"script-src 'sha256-[^']+'",lambda _:"script-src 'sha256-"+digest+"'",text)
 (ROOT/'site/index.html').write_text(text,encoding='utf-8')
 names=['index.html','data/current-state.json','data/market.json','reports/2026-09-11-carry-forward.md','data/macro.json','data/macro-calendar.json']
 m={'version':2,'classification':'public-market-research','files':{n:hashlib.sha256((ROOT/'site'/n).read_bytes()).hexdigest() for n in names}};(ROOT/'site/manifest.json').write_text(json.dumps(m,indent=2)+'\n');return text
if __name__=='__main__':build();print('Built v0.6 from validated source snapshots')
