#!/usr/bin/env python3
"""Finalize dashboard UI after deterministic data build without changing market-data rights."""
import argparse,base64,hashlib,html,json,re,os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

BADGE_OLD="badge('ARCHIVE SNAPSHOT / '+D.as_of,'p-warn')"
BADGE_NEW="badge('MARKET LIVE / PROVIDER-HOSTED','p-good')"
AGE_OLD="株価・指数: 2026-09-10固定 / マクロ: 各系列の観測日 / カレンダー: Source Healthを確認"
AGE_NEW="株価・指数: TradingView live（市場によりリアルタイム・遅延・EOD） / マクロ: 各系列の観測日 / カレンダー: Source Healthを確認"

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

def health_panel(macro,report):
 series=macro.get('series',[]);public=[s for s in series if s.get('id')!='vix']
 fresh=sum(s.get('status')=='available' for s in public);total=len(public)
 statuses=[v for fam in (report.get('family_year_status') or {}).values() for v in fam.values()]
 if any(x=='degraded' for x in statuses):cal='DEGRADED';cal_cls='pending'
 elif any(x=='source_access_blocked' for x in statuses):cal='PARTIAL ACCESS';cal_cls='pending'
 elif report.get('mode')=='family_merge':cal='FAMILY MERGE';cal_cls='good'
 else:cal='REVIEWED STATIC';cal_cls='pending'
 macro_cls='good' if total and fresh==total else 'pending';run=os.environ.get('GITHUB_RUN_ID','not-recorded')
 return ('<section data-dashboard-health="true" class="p-card"><div class="eyebrow">DASHBOARD HEALTH / CURRENT BUILD</div>'
         '<h3>更新・取得・公開の状態</h3><div class="grid four">'
         f'<article class="card"><div class="eyebrow">MACRO</div><div class="metric {macro_cls}">{fresh}/{total} fresh</div><p class="small">最終取得試行 {html.escape(jst(macro.get("attempted_at","")))}</p></article>'
         f'<article class="card"><div class="eyebrow">CALENDAR</div><div class="metric {cal_cls}">{cal}</div><p class="small">完全性ゲートを維持。取得障害時はレビュー済み日程を保持。</p></article>'
         '<article class="card"><div class="eyebrow">MARKET</div><div class="metric good">LIVE VIEW</div><p class="small">TradingView provider-hosted。自己ホスト価格は権利ゲートで凍結し、通常表示から除外。</p></article>'
         '<article class="card"><div class="eyebrow">BROWSER QA</div><div class="metric good">FAIL-CLOSED</div><p class="small">Chrome起動タイムアウトのみ最大1回再試行。その他の異常は公開停止。</p></article>'
         '</div><p class="small">定期実行: JST 01:17 / 07:17 / 13:17 / 19:17 ・ Run '+html.escape(run)+' ・ 履歴成功率の蓄積表示は次段階。</p></section>')

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

def apply(text,macro):
 if 'data-dashboard-health="true"' in text:return text
 if BADGE_OLD not in text or AGE_OLD not in text:raise ValueError('market status markers')
 text=text.replace(BADGE_OLD,BADGE_NEW,1).replace(AGE_OLD,AGE_NEW,1)
 text=text.replace('下段の2026-09-10固定値は監査用スナップショットです。','旧固定値は監査用に内部保持し、通常画面では非表示です。',1)
 text=text.replace('下段の2026-09-10以前の値は監査用スナップショットです。','旧固定値は監査用に内部保持し、通常画面では非表示です。',1)
 text=hide_legacy_panel(text,'world','market');text=hide_legacy_panel(text,'market','events')
 marker='<section class="panel" id="operations" aria-labelledby="tab-operations"><h2>出典・運用</h2>'
 if text.count(marker)!=1:raise ValueError('operations marker')
 text=text.replace(marker,marker+health_panel(macro,calendar_report(text)),1)
 return refresh_csp(text)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--site',default='site');a=ap.parse_args()
 site=Path(a.site);idx=site/'index.html';macro=json.loads((site/'data/macro.json').read_text());out=apply(idx.read_text(),macro)
 if a.apply:idx.write_text(out)
 print(json.dumps({'dashboard_health':'embedded','market_primary':'provider_hosted_live','legacy_market':'hidden','macro_attempted_at':macro.get('attempted_at')},ensure_ascii=False))
if __name__=='__main__':main()
