#!/usr/bin/env python3
"""Finalize dashboard UI after deterministic data build without changing market-data rights."""
import argparse,base64,hashlib,html,json,re,os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import release_state as state_contract

BADGE_OLD="badge('ARCHIVE SNAPSHOT / '+D.as_of,'p-warn')"
BADGE_NEW="badge('MARKET / PROVIDER-HOSTED','p-good')"
AGE_OLD="株価・指数: 2026-09-10固定 / マクロ: 各系列の観測日 / カレンダー: Source Healthを確認"
AGE_NEW="株価・指数: TradingView provider-hosted（配信応答はビルド未検証） / マクロ: 各系列の観測日 / カレンダー: Source Healthを確認"
HEADER_OLD="v0.4.0 / 2026-09-13 / 世界指数・株価分析"
HEADER_NEW="v0.6.0 / 公開版 / MARKET PROVIDER-HOSTED + MACRO AUTO REFRESH"
STATIC_AGE_OLD="日程確認：2026-09-13 / 自動更新ではありません"
STATIC_AGE_NEW="株価・指数: TradingView provider-hosted（価格応答は未検証） / マクロ: 1日4回更新 / カレンダー: Source Healthを確認"
EVENT_NOTE_OLD="2026年9月13日に公式掲載日程を確認。変更される場合があります。会合は開催地の日付、統計は日本時間を併記します。"
EVENT_NOTE_NEW="このタブの固定8件は2026-09-13レビュー時点。最新の日程確認は「マクロ」の経済カレンダー / Source Healthを参照。会合は開催地の日付、統計は日本時間を併記します。"
SAFETY_OLD="外部接続とフォーム送信を禁止するブラウザ設定を入れています。"
SAFETY_NEW="TradingView公式Widgetの許可済み接続を除き、任意の外部接続とフォーム送信をCSPで禁止しています。"

def jst(iso):
 try:
  return datetime.fromisoformat(iso.replace('Z','+00:00')).astimezone(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M JST')
 except Exception:
  return '確認が必要'

def calendar_report(text):
 m=re.search(r'<pre id="macro-calendar-report" hidden>(.*?)</pre>',text,re.S)
 if not m:return {}
 try:return json.loads(html.unescape(m.group(1)))
 except Exception:return {}

def _calendar_health(report):
 statuses=[v for fam in (report.get('family_year_status') or {}).values() for v in fam.values()]
 if any(x=='degraded' for x in statuses):return 'degraded'
 if statuses and all(x=='source_access_blocked' for x in statuses):return 'source_access_blocked'
 if any(x=='source_access_blocked' for x in statuses):return 'partial_access_blocked'
 if report.get('mode')=='family_merge':return 'fresh'
 return 'reviewed_static'

def operational_state(macro,market,report):
 series=macro.get('series',[]);public=[s for s in series if s.get('id')!='vix']
 fresh=sum(s.get('status')=='available' for s in public);total=len(public)
 retained=any(s.get('status')=='retained' for s in public)
 macro_freshness='fresh' if total and fresh==total else ('retained' if retained else 'stale')
 cal_health=_calendar_health(report)
 cal_module='available' if cal_health=='fresh' else ('blocked' if cal_health=='source_access_blocked' else ('reviewed_static' if cal_health=='reviewed_static' else 'degraded'))
 run=os.environ.get('GITHUB_RUN_ID')
 if not (run and run.isdigit()):run=None
 result={
  'schema_version':state_contract.SCHEMA_VERSION,
  'release':{'version':'0.6.0','channel':'public','verified_at':None,'build_run_id':run},
  'market':{
   'delivery_mode':'provider_hosted','quote_observation':'not_observed_by_build','data_persisted':False,
   'snapshot_as_of':market.get('as_of'),'freshness':'unknown'},
  'macro':{'attempted_at':macro.get('attempted_at'),'available_count':fresh,'total_count':total,'freshness':macro_freshness},
  'calendar':{'source_health':cal_health,'mode':str(report.get('mode') or 'reviewed_static'),'verified_at':None},
  'event':{'active_event_ids':[],'phase':'reviewed_static_policy_watch','phase_verified_at':None},
  'modules':{'market':'available','macro':'available' if macro_freshness=='fresh' else 'degraded','calendar':cal_module,'events':'reviewed_static','research':'reviewed_static'},
  'publication':{'legacy_market_public_presence':'published','legacy_market_visibility':'hidden','use_legacy_market_for_current_decisions':False},
 }
 return state_contract.validate(result)

def health_panel(state):
 macro=state['macro'];cal_health=state['calendar']['source_health'];run=state['release']['build_run_id'] or 'not-recorded'
 cal_map={
  'degraded':('DEGRADED','pending'),
  'partial_access_blocked':('PARTIAL ACCESS','pending'),
  'source_access_blocked':('ACCESS BLOCKED','pending'),
  'fresh':('FAMILY MERGE','good'),
  'reviewed_static':('REVIEWED STATIC','pending'),
  'unknown':('UNKNOWN','pending'),
 }
 cal,cal_cls=cal_map[cal_health];macro_cls='good' if macro['freshness']=='fresh' else 'pending'
 presence='公開HTML内に保持' if state['publication']['legacy_market_public_presence']=='published' else '公開物から除外'
 visibility='画面非表示' if state['publication']['legacy_market_visibility']=='hidden' else '画面表示'
 return ('<section data-dashboard-health="true" class="p-card"><div class="eyebrow">DASHBOARD HEALTH / CURRENT BUILD</div>'
         '<h3>更新・取得・公開の状態</h3><div class="grid four">'
         f'<article class="card"><div class="eyebrow">MACRO</div><div class="metric {macro_cls}">{macro["available_count"]}/{macro["total_count"]} fresh</div><p class="small">最終取得試行 {html.escape(jst(macro.get("attempted_at") or ""))}</p></article>'
         f'<article class="card"><div class="eyebrow">CALENDAR</div><div class="metric {cal_cls}">{cal}</div><p class="small">完全性ゲートを維持。取得障害時はレビュー済み日程を保持。</p></article>'
         '<article class="card"><div class="eyebrow">MARKET</div><div class="metric pending">PROVIDER-HOSTED</div><p class="small">TradingView埋込を公開。CIは外部価格応答を遮断するため、表示価格の到達・鮮度は当ビルドでは検証しません。</p></article>'
         '<article class="card"><div class="eyebrow">BROWSER QA</div><div class="metric good">FAIL-CLOSED</div><p class="small">Chrome起動タイムアウトのみ最大1回再試行。その他の異常は公開停止。</p></article>'
         f'</div><p class="small" data-market-publication-state="true">旧自己ホスト市場データ: {presence} / {visibility} / 現在値判断には不使用。</p>'
         '<p class="small">定期実行: JST 01:17 / 07:17 / 13:17 / 19:17 ・ Run '+html.escape(str(run))+' ・ 履歴成功率の蓄積表示は次段階。</p></section>')

def hide_legacy_panel(text,panel_id,next_id):
 start=text.index(f'<section class="panel" id="{panel_id}"');next_start=text.index(f'<section class="panel" id="{next_id}"',start)
 seg=text[start:next_start];marker='<div data-market-archive="true" class="notice">';p=seg.index(marker);q=seg.index('</div>',p)+len('</div>');outer=seg.rfind('</section>')
 if outer<=q:raise ValueError('market archive boundary')
 legacy=seg[q:outer]
 notice=('<div data-market-archive="true" class="notice"><strong>旧自己ホスト市場データは監査用に内部保持</strong><br>'
         '2026-09-10以前の固定値は通常表示から除外しました。現在の市場確認は上段のTradingView Widgetを使用してください。</div>')
 seg=seg[:p]+notice+'<div data-market-legacy="true" hidden aria-hidden="true">'+legacy+'</div>'+seg[outer:]
 return text[:start]+seg+text[next_start:]

def refresh_csp(text):
 scripts=re.findall(r'<script\b([^>]*)>(.*?)</script\s*>',text,re.I|re.S);inline=[body for attrs,body in scripts if 'src=' not in attrs.lower()]
 if len(inline)!=1:raise ValueError('inline script count')
 digest=base64.b64encode(hashlib.sha256(inline[0].encode()).digest()).decode()
 return re.sub(r"script-src 'sha256-[^']+'","script-src 'sha256-"+digest+"'",text,count=1)

def replace_exact(text,old,new,label):
 if text.count(old)!=1:raise ValueError(label)
 return text.replace(old,new,1)

def apply(text,macro,market):
 if 'data-dashboard-health="true"' in text:return text
 if BADGE_OLD not in text or AGE_OLD not in text:raise ValueError('market status markers')
 text=text.replace(BADGE_OLD,BADGE_NEW,1).replace(AGE_OLD,AGE_NEW,1)
 text=replace_exact(text,HEADER_OLD,HEADER_NEW,'header release marker')
 text=replace_exact(text,STATIC_AGE_OLD,STATIC_AGE_NEW,'static freshness marker')
 text=replace_exact(text,EVENT_NOTE_OLD,EVENT_NOTE_NEW,'event freshness note')
 text=replace_exact(text,SAFETY_OLD,SAFETY_NEW,'frontend connection note')
 text=text.replace('下段の2026-09-10固定値は監査用スナップショットです。','旧固定値は監査用に内部保持し、通常画面では非表示です。',1)
 text=text.replace('下段の2026-09-10以前の値は監査用スナップショットです。','旧固定値は監査用に内部保持し、通常画面では非表示です。',1)
 text=hide_legacy_panel(text,'world','market');text=hide_legacy_panel(text,'market','events')
 marker='<section class="panel" id="operations" aria-labelledby="tab-operations"><h2>出典・運用</h2>'
 if text.count(marker)!=1:raise ValueError('operations marker')
 current=operational_state(macro,market,calendar_report(text))
 text=text.replace(marker,marker+health_panel(current),1)
 return refresh_csp(text)

def sync_manifest(site,index_bytes):
 path=site/'manifest.json';manifest=json.loads(path.read_text());files=manifest.get('files')
 if not isinstance(files,dict) or 'index.html' not in files:raise ValueError('manifest index entry')
 files['index.html']=hashlib.sha256(index_bytes).hexdigest()
 path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--site',default='site');a=ap.parse_args()
 site=Path(a.site);idx=site/'index.html';macro=json.loads((site/'data/macro.json').read_text());market=json.loads((site/'data/market.json').read_text());out=apply(idx.read_text(),macro,market)
 if a.apply:
  encoded=out.encode();idx.write_bytes(encoded);sync_manifest(site,encoded)
 current=operational_state(macro,market,calendar_report(out))
 print(json.dumps({'dashboard_health':'embedded','release_state_schema':current['schema_version'],'market_delivery':current['market']['delivery_mode'],'market_quote_observation':current['market']['quote_observation'],'legacy_market_public_presence':current['publication']['legacy_market_public_presence'],'legacy_market_visibility':current['publication']['legacy_market_visibility'],'macro_attempted_at':macro.get('attempted_at')},ensure_ascii=False))
if __name__=='__main__':main()
