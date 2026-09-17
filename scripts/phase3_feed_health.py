#!/usr/bin/env python3
"""v0.7 Market Feed Health Phase 1 presentation.

Adds an explicit feed-health layer without claiming quote freshness that the build
cannot observe. Provider-hosted TradingView delivery is kept separate from quote
mode (real-time / delayed / EOD), and official macro retrieval status is rendered
from the validated macro snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from html import escape
from pathlib import Path

import phase2_overview

ROOT=Path(__file__).resolve().parents[1]
MARKER='data-market-feed-health="true"'
PHASE5='EXECUTIVE OVERVIEW / v0.7 PHASE 5'
PHASE6='EXECUTIVE OVERVIEW / v0.7 PHASE 6'
INSERT_BEFORE='<section data-relevance-scoring="true" class="card full">'

PROVIDER_FEEDS=(
 ('world','世界指数','world','TradingView market overview'),
 ('stocks','主要株・ETF','market','TradingView market overview'),
 ('policy','政策反応','events','TradingView policy reaction board'),
)
STATUS_LABELS={
 'available':('SOURCE OK','good','公式ソース取得成功'),
 'retained':('RETAINED','pending','今回の取得失敗。直前の検証済み値を保持'),
 'unavailable':('UNAVAILABLE','pending','取得できず、公開可能な保持値もなし'),
 'rights_pending':('RIGHTS PENDING','pending','権利確認前のため値を公開しない'),
}


def _latest(series):
 rows=series.get('observations') or []
 return rows[-1][0] if rows else '--'


def _fetched(series):
 value=series.get('fetched_at')
 return value if value is not None else '--'


def feed_health_block(macro_data):
 series=macro_data['series']
 available=sum(s['status']=='available' for s in series if s['id']!='vix')
 retained=sum(s['status']=='retained' for s in series if s['id']!='vix')
 unavailable=sum(s['status']=='unavailable' for s in series if s['id']!='vix')
 provider=''.join(
  '<article class="card" data-market-feed="'+escape(feed_id)+'" data-feed-delivery="provider_hosted" data-quote-mode="provider_determined">'
  '<div class="eyebrow">'+escape(label)+'</div><div class="metric good">PROVIDER-HOSTED</div>'
  '<p>'+escape(product)+'</p><p class="small">Delivery: 閲覧時に外部Providerへ接続。Quote mode: real-time / delayed / EODはProvider・取引所条件で決まり、当ビルドは判定しません。Current quoteは保存・再配布せず、Archiveへの自動fallbackもしません。</p>'
  '<button type="button" class="p-link-button" data-feed-target="'+escape(target)+'">対応タブで確認</button></article>'
  for feed_id,label,target,product in PROVIDER_FEEDS
 )
 macro=''.join(
  '<li data-macro-feed="'+escape(s['id'])+'" data-source-status="'+escape(s['status'])+'">'
  '<strong>'+escape(s['id'].upper())+'</strong> <span class="tag '+STATUS_LABELS[s['status']][1]+'">'+STATUS_LABELS[s['status']][0]+'</span><br>'
  '<span class="small">'+STATUS_LABELS[s['status']][2]+' ・ Last observation '+escape(_latest(s))+' ・ Last successful retrieval '+escape(_fetched(s))+'</span></li>'
  for s in series
 )
 wti=next(s for s in series if s['id']=='wti')
 return (
  '<section '+MARKER+' class="card full"><div class="eyebrow">MARKET FEED HEALTH / DELIVERY ≠ FRESHNESS</div><h3>ライブ表示・公的データ・監査Archiveを分離</h3>'
  '<div class="notice"><strong>現在値の扱い:</strong> TradingView Widgetはprovider-hostedです。当サイトはWidgetが表示する個別quoteをbuild時に観測できないため、「リアルタイム」「遅延」「EOD」を推測で固定しません。画面上のProvider表示を確認してください。</div>'
  '<div class="grid three">'+provider+'</div>'
  '<div class="grid four">'
  '<article class="card"><div class="eyebrow">Official macro available</div><div class="metric">'+str(available)+'</div><p class="small">VIXを除く6系列中</p></article>'
  '<article class="card"><div class="eyebrow">Retained</div><div class="metric '+('pending' if retained else 'good')+'">'+str(retained)+'</div><p class="small">取得失敗時の検証済み保持値</p></article>'
  '<article class="card"><div class="eyebrow">Unavailable</div><div class="metric '+('pending' if unavailable else 'good')+'">'+str(unavailable)+'</div><p class="small">保持値もない系列</p></article>'
  '<article class="card"><div class="eyebrow">WTI</div><div class="metric '+STATUS_LABELS[wti['status']][1]+'">'+STATUS_LABELS[wti['status']][0]+'</div><p class="small">Last observation '+escape(_latest(wti))+'</p></article></div>'
  '<article class="card"><div class="eyebrow">OFFICIAL MACRO SOURCE HEALTH</div><ul>'+macro+'</ul></article>'
  '<p class="small">Archive snapshotは監査用であり、Provider障害時にcurrent quoteへ昇格しません。Source retrieval successも「新しい観測値が出た」ことを意味しません。</p></section>'
 )


def apply(text,macro_data):
 if MARKER in text:return text
 if text.count(phase2_overview.MARKER)!=1 or text.count(PHASE5)!=1 or text.count(INSERT_BEFORE)!=1:raise ValueError('phase3 anchor')
 text=text.replace(PHASE5,PHASE6,1)
 text=text.replace(INSERT_BEFORE,feed_health_block(macro_data)+INSERT_BEFORE,1)
 return text


def sync_manifest(site,index_bytes):
 path=site/'manifest.json';manifest=json.loads(path.read_text(encoding='utf-8'));files=manifest.get('files')
 if not isinstance(files,dict) or 'index.html' not in files:raise ValueError('manifest index')
 files['index.html']=hashlib.sha256(index_bytes).hexdigest();path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--path',default=str(ROOT/'site/index.html'));args=ap.parse_args();path=Path(args.path);macro=json.loads((path.parent/'data/macro.json').read_text(encoding='utf-8'));out=apply(path.read_text(encoding='utf-8'),macro)
 if args.apply:
  data=out.encode();path.write_bytes(data);sync_manifest(path.parent,data)
 else:print(out)

if __name__=='__main__':main()
