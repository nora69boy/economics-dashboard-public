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
TV_SCRIPT='https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js'
TV_MARKETS='https://www.tradingview.com/markets/'
BOJ_RELEASE='https://www.boj.or.jp/about/calendar/index.htm'
POLICY_JS="""
(()=>{
'use strict';
const stage=document.getElementById('policy-stage'),countdown=document.getElementById('policy-countdown');if(!stage||!countdown)return;
const fomc=Date.parse('2026-09-17T03:00:00+09:00'),fomcPc=Date.parse('2026-09-17T03:30:00+09:00'),bojPc=Date.parse('2026-09-18T15:30:00+09:00');
function left(t,n){const m=Math.max(0,Math.floor((t-n)/60000)),d=Math.floor(m/1440),h=Math.floor((m%1440)/60),x=m%60;return (d?d+'日 ':'')+h+'時間 '+x+'分';}
function render(){const n=Date.now();if(n<fomc){stage.textContent='FOMC声明待ち';countdown.textContent='FOMC声明まで '+left(fomc,n);}else if(n<fomcPc){stage.textContent='FOMC声明公表 / 議長会見待ち';countdown.textContent='議長会見まで '+left(fomcPc,n);}else if(n<bojPc){stage.textContent='FOMC通過 / 日銀決定・会見監視';countdown.textContent='日銀総裁会見まで '+left(bojPc,n)+'（政策決定内容の公表時刻は未定）';}else{stage.textContent='FOMC・日銀通過後 / 市場反応を検証';countdown.textContent='金利・USD/JPY・TOPIX・日経225の24時間反応を確認';}}
render();setInterval(render,60000);
})();
"""

def market_rights_health():
 registry=json.loads((ROOT/'data-rights/registry.json').read_text())
 market=json.loads((ROOT/'site/data/market.json').read_text())
 report=market_refresh_guard.evaluate(registry,market)
 cards=[]
 for stage in report['stages']:
  ready=stage['status']=='ready';total=stage['eligible_count']+stage['blocked_count']
  label='無料自動更新可能' if ready else '無料運用：凍結'
  cls='good' if ready else 'pending'
  cards.append('<article class="card" data-market-rights-stage="'+escape(stage['stage'])+'" data-market-rights-status="'+escape(stage['status'])+'"><div class="eyebrow">'+escape(STAGE_LABELS[stage['stage']])+'</div><div class="metric '+cls+'">'+label+'</div><p>'+str(stage['eligible_count'])+' / '+str(total)+' 系列が月額0円かつ公開自動更新の権利条件を満たす。</p><p class="small">無料で自動取得・保存・加工・公開表示・再配布・キャッシュの全条件を満たさない限り自己ホスト値は更新しません。</p></article>')
 return '<h2>無料運用モード / 市場データ</h2><div class="notice" data-market-free-mode="true"><strong>月額0円運用を固定。自己ホストの株価・指数は監査用凍結スナップショットを維持します。</strong><br>主表示はTradingView公式Widgetでライブ更新しますが、価格データをこのリポジトリへ保存・再配布しません。有料API・有料ライセンスの比較や導入は行いません。現在の自己ホスト株価・指数スナップショット基準日：'+escape(report['snapshot_as_of'])+'</div><div class="grid two" id="market-rights-health">'+''.join(cards)+'</div>'

def tv_widget(kind):
 if kind=='indices':
  title='株価指数 / ライブ更新（主表示）'
  note='TradingView配信。市場・取引所・契約条件によりリアルタイム、遅延、またはEODとなります。下段の2026-09-10固定値は監査用スナップショットです。'
  symbols=[
   {'s':'TVC:SPX','d':'S&P 500'}, {'s':'NASDAQ:IXIC','d':'NASDAQ Composite'},
   {'s':'TVC:DJI','d':'Dow Jones'}, {'s':'TVC:NI225','d':'Nikkei 225'},
   {'s':'TSE:TOPIX','d':'TOPIX'}, {'s':'XETR:DAX','d':'DAX'},
   {'s':'FTSE:UKX','d':'FTSE 100'}, {'s':'HSI:HSI','d':'Hang Seng'},
   {'s':'KRX:KOSPI','d':'KOSPI'}]
  shell='live-market-indices'
 else:
  title='主要株・ETF / ライブ更新（主表示）'
  note='TradingView配信。価格の保存・再配布はこのリポジトリでは行いません。下段の2026-09-10以前の値は監査用スナップショットです。'
  symbols=[
   {'s':'NASDAQ:NVDA','d':'NVIDIA'}, {'s':'NASDAQ:MSFT','d':'Microsoft'},
   {'s':'NASDAQ:AAPL','d':'Apple'}, {'s':'NASDAQ:GOOGL','d':'Alphabet'},
   {'s':'NASDAQ:AMZN','d':'Amazon'}, {'s':'AMEX:SPY','d':'SPDR S&P 500 ETF'}]
  shell='live-market-stocks'
 cfg={'colorTheme':'dark','dateRange':'1D','locale':'ja','largeChartUrl':'','isTransparent':True,
      'showFloatingTooltip':True,'plotLineColorGrowing':'rgba(105,222,200,1)',
      'plotLineColorFalling':'rgba(245,173,193,1)','gridLineColor':'rgba(49,70,94,0.25)',
      'scaleFontColor':'#b5c4d5','belowLineFillColorGrowing':'rgba(105,222,200,0.12)',
      'belowLineFillColorFalling':'rgba(245,173,193,0.12)',
      'belowLineFillColorGrowingBottom':'rgba(105,222,200,0.02)',
      'belowLineFillColorFallingBottom':'rgba(245,173,193,0.02)',
      'symbolActiveColor':'rgba(146,202,255,0.12)','tabs':[{'title':title,'symbols':symbols}],
      'width':'100%','height':'550','showSymbolLogo':True,'showChart':True}
 return ('<section data-rights-shell="'+shell+'" class="p-card live-market-widget">'
         '<h3>'+escape(title)+'</h3><div class="notice"><strong>ライブ更新へ切替済み。</strong> '+escape(note)+'</div>'
         '<div class="tradingview-widget-container" style="width:100%;min-height:550px">'
         '<div class="tradingview-widget-container__widget"></div>'
         '<div class="tradingview-widget-copyright"><a href="'+TV_MARKETS+'" rel="noopener noreferrer nofollow" referrerpolicy="no-referrer" target="_blank">Market data</a> by TradingView</div>'
         '<script type="text/javascript" src="'+TV_SCRIPT+'" async>'+json.dumps(cfg,ensure_ascii=False,separators=(',',':'))+'</script>'
         '</div><p class="small">外部Widgetのため閲覧時にTradingViewへ通信します。表示値は当サイトの保存データではありません。</p></section>')

def policy_watch():
 fed='https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'
 boj='https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm'
 return ('<section data-rights-shell="policy-watch" class="p-card"><div class="eyebrow">POLICY EVENT WATCH / 2026-09</div>'
         '<h3>FOMC × 日銀 イベント駆動パネル</h3><div class="notice"><strong id="policy-stage">FOMC声明待ち</strong><br><span id="policy-countdown" aria-live="polite">時刻を計算中</span><br>時刻未定の公表は推測で補完しません。</div>'
         '<div class="grid two"><article class="card"><h3>FOMC</h3><p><strong>9/15–16（米東部）</strong></p><p>政策声明：9/16 14:00 ET → <strong>9/17 03:00 JST</strong><br>議長会見：14:30 ET → <strong>03:30 JST</strong></p><p class="small">監視：米10年金利、USD/JPY、NASDAQ/S&P 500。声明→会見で方向が反転する場合は初動を確定シグナルと扱わない。</p><p><a href="'+fed+'" rel="noopener noreferrer" referrerpolicy="no-referrer">FRB公式日程</a></p></article>'
         '<article class="card"><h3>日本銀行</h3><p><strong>9/17–18 JST</strong></p><p>金融政策決定内容：9/18 <strong>時刻未定</strong><br>植田総裁会見：<strong>9/18 15:30 JST</strong></p><p class="small">監視：USD/JPY、TOPIX、日経225。決定公表時刻は未定のため、時刻を仮定した自動売買判断はしない。</p><p><a href="'+boj+'" rel="noopener noreferrer" referrerpolicy="no-referrer">日銀会合日程</a> / <a href="'+BOJ_RELEASE+'" rel="noopener noreferrer" referrerpolicy="no-referrer">日銀公表予定</a></p></article></div>'
         '<div class="grid"><article class="card"><h3>楽観シナリオ</h3><p>Fedが過度にタカ派化せず、日銀も急激な引締めを避ける。金利・円の急変が抑えられればグロース株のバリュエーション圧力が緩和。</p></article>'
         '<article class="card"><h3>標準シナリオ</h3><p>政策変更よりガイダンスの差分が中心。声明直後ではなく、FOMC会見後とBOJ会見後の金利・為替の方向一致を確認。</p></article>'
         '<article class="card"><h3>悲観シナリオ</h3><p>Fedタカ派化と日銀引締め方向が重なり、金利・円・株式が同時に大きく再評価。高PERグロースと円キャリー依存の巻き戻しに注意。</p></article></div>'
         '<p class="small">最大リスク：声明・会見間のヘッドライン反転。見落としやすいリスク：市場が政策変更を事前織込み済みで、結果が「予想通り」でも逆方向に動くこと。反証材料：金利・為替・株式の反応が24時間以内に解消し、イベント前レンジへ戻る場合。</p></section>')

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
 text=text.replace('個人に紐づく金融情報や秘密情報の入力・保存・掲載は行いません。広告・解析タグ・外部画像・外部プログラムはありません。','個人に紐づく金融情報や秘密情報の入力・保存・掲載は行いません。広告・解析タグ・フォーム送信はありません。ライブ市場表示に限りTradingView公式Widgetを読み込みます。')
 text=text.replace('出典リンクを押すと、その外部サイトへ移動します。リンクを押さない限り、アプリによる外部通信は行いません。','ライブ市場Widgetは表示時にTradingViewへ通信します。その他の出典リンクは押したときだけ外部サイトへ移動します。')
 marker='<section class="panel" id="operations" aria-labelledby="tab-operations"><h2>出典・運用</h2>'
 if text.count(marker)!=1:raise ValueError('operations marker')
 text=text.replace(marker,marker+market_rights_health(),1)
 embedded='<pre id="macro-data" hidden>'+escape(md)+'</pre><pre id="macro-calendar-data" hidden>'+escape(cd)+'</pre><pre id="macro-calendar-report" hidden>'+escape(cr)+'</pre>'
 fallback='<noscript><article><h2>Macro data / JavaScript disabled</h2><p>Static observations only. VIX withheld pending republication permission. Calendar and charts require JavaScript.</p><table><thead><tr><th>Series</th><th>Observation date</th><th>Raw value</th><th>Status</th></tr></thead><tbody>'
 for s in macro['series']:
  latest=s['observations'][-1] if s['observations'] else ['--','--'];fallback+='<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in [s['id'],*latest,s['status']])+'</tr>'
 fallback+='</tbody></table></article></noscript>';text=text.replace('</body>',embedded+fallback+'</body>')
 code=re.findall(r'<script[^>]*>(.*?)</script>',text,re.S)[0]+'\n'+(ROOT/'templates/macro.js').read_text()+'\n'+POLICY_JS
 text=re.sub(r'<script[^>]*>.*?</script>',lambda _:'<script>'+code+'</script>',text,flags=re.S)
 script='<script>'+code+'</script>';text=text.replace(script,'').replace('</body>',script+'</body>');text=text.replace('</style>',(ROOT/'templates/macro.css').read_text()+'</style>',1)
 digest=base64.b64encode(hashlib.sha256(code.encode()).digest()).decode();text=re.sub(r"script-src 'sha256-[^']+'",lambda _:"script-src 'sha256-"+digest+"'",text)
 world_marker='<section class="panel" id="world" aria-labelledby="tab-world"><h2>世界の株価指数</h2>'
 market_marker='<section class="panel" id="market" aria-labelledby="tab-market"><h2>個別株・ETF・決算</h2>'
 event_marker='<section class="panel" id="events" aria-labelledby="tab-events"><h2>イベント</h2>'
 if any(text.count(x)!=1 for x in [world_marker,market_marker,event_marker]):raise ValueError('live widget marker')
 text=text.replace(world_marker,world_marker+tv_widget('indices'),1)
 text=text.replace(market_marker,market_marker+tv_widget('stocks'),1)
 text=text.replace(event_marker,event_marker+policy_watch(),1)
 text=text.replace("script-src 'sha256-"+digest+"';","script-src 'sha256-"+digest+"' https://s3.tradingview.com;",1)
 text=text.replace("frame-src 'none';","frame-src https://s.tradingview.com https://www.tradingview.com https://www.tradingview-widget.com;",1)
 (ROOT/'site/index.html').write_text(text,encoding='utf-8')
 names=['index.html','data/current-state.json','data/market.json','reports/2026-09-11-carry-forward.md','data/macro.json','data/macro-calendar.json']
 m={'version':2,'classification':'public-market-research','files':{n:hashlib.sha256((ROOT/'site'/n).read_bytes()).hexdigest() for n in names}};(ROOT/'site/manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 print('Calendar publication '+json.dumps(calendar_report,sort_keys=True,separators=(',',':')))
 print('Market rights health '+json.dumps(market_refresh_guard.evaluate(json.loads((ROOT/'data-rights/registry.json').read_text()),json.loads((ROOT/'site/data/market.json').read_text())),sort_keys=True,separators=(',',':')))
 return text
if __name__=='__main__':build();print('Built v0.6 with live widgets and policy watch')
