"""Reproducible v0.6 build from versioned templates and validated public numeric snapshots."""
import base64,hashlib,json,re
from html import escape
from pathlib import Path
import build_dashboard,calendar_publish,market_refresh_guard
from macro_core import validate,validate_calendar
ROOT=Path(__file__).resolve().parents[1]

STAGE_LABELS={
 'us_stocks':'米国株',
 'us_etf':'米国ETF',
 'us_indices':'米国指数',
 'japan_indices':'日本指数',
 'europe_indices':'欧州指数',
 'asia_indices':'アジア・豪州指数',
}

def market_rights_health():
 registry=json.loads((ROOT/'data-rights/registry.json').read_text())
 market=json.loads((ROOT/'site/data/market.json').read_text())
 report=market_refresh_guard.evaluate(registry,market)
 cards=[]
 for stage in report['stages']:
  ready=stage['status']=='ready';total=stage['eligible_count']+stage['blocked_count']
  label='自動更新可能' if ready else '権利確認待ち'
  cls='good' if ready else 'pending'
  cards.append('<article class="card" data-market-rights-stage="'+escape(stage['stage'])+'" data-market-rights-status="'+escape(stage['status'])+'"><div class="eyebrow">'+escape(STAGE_LABELS[stage['stage']])+'</div><div class="metric '+cls+'">'+label+'</div><p>'+str(stage['eligible_count'])+' / '+str(total)+' 系列が公開自動更新の権利条件を満たす。</p><p class="small">自動取得・保存・加工・公開表示・再配布・キャッシュの全条件が必要。</p></article>')
 return '<h2>市場データ権利 / 自動更新</h2><div class="notice"><strong>株価・指数は権利確認が完了するまで凍結スナップショットを維持します。</strong><br>APIが利用可能でも、公開表示・再配布まで明示許諾されていなければ自動更新しません。現在のスナップショット基準日：'+escape(report['snapshot_as_of'])+'</div><div class="grid two" id="market-rights-health">'+''.join(cards)+'</div>'

def build():
 md=(ROOT/'site/data/macro.json').read_text();calendar,calendar_report=calendar_publish.build();cd=json.dumps(calendar,separators=(',',':'))+'\n';cr=json.dumps(calendar_report,separators=(',',':'))+'\n';(ROOT/'site/data/macro-calendar.json').write_text(cd)
 macro=json.loads(md);cal=json.loads(cd);validate(macro);validate_calendar(cal);text=build_dashboard.build()
 start=text.index('// Data coverage is a measured inventory, never a fictional market reading.');end=text.index("const operations=$('operations');",start)
 text=text[:start]+'// Macro history rendered by the independent typed-data module.\n'+text[end:]
 text=text.replace("badge('SNAPSHOT / '","badge('STOCK SNAPSHOT / '")
 text=text.replace('v0.5.0','v0.6.0').replace("version:'0.5.0'","version:'0.6.0'")
 text=text.replace("const archive=$('archive');archive.append(card('v0.6.0 /", "const archive=$('archive');archive.append(card('v0.5.0 /")
 text=text.replace("['0','接続済み自動取得','リアルタイム値なし']","['6','マクロ自動取得系列','公的データ / 株価は対象外']")
 text=text.replace('自動更新なし / 追跡タグなし','マクロのみ定期取得 / 追跡タグなし')
 marker='<section class="panel" id="operations" aria-labelledby="tab-operations"><h2>出典・運用</h2>'
 if text.count(marker)!=1:raise ValueError('operations marker')
 text=text.replace(marker,marker+market_rights_health(),1)
 embedded='<pre id="macro-data" hidden>'+escape(md)+'</pre><pre id="macro-calendar-data" hidden>'+escape(cd)+'</pre><pre id="macro-calendar-report" hidden>'+escape(cr)+'</pre>'
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
 m={'version':2,'classification':'public-market-research','files':{n:hashlib.sha256((ROOT/'site'/n).read_bytes()).hexdigest() for n in names}};(ROOT/'site/manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 print('Calendar publication '+json.dumps(calendar_report,sort_keys=True,separators=(',',':')))
 print('Market rights health '+json.dumps(market_refresh_guard.evaluate(json.loads((ROOT/'data-rights/registry.json').read_text()),json.loads((ROOT/'site/data/market.json').read_text())),sort_keys=True,separators=(',',':')))
 return text
if __name__=='__main__':build();print('Built v0.6 from validated source snapshots')
