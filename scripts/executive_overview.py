#!/usr/bin/env python3
"""Inject the v0.7 Executive Overview into the reviewed public HTML.

The panel is derived from typed policy-event records plus reviewed identity-only
systemic registry records. It adds no new market-data transport or self-hosted
quote payloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from html import escape
from pathlib import Path

import policy_events
import systemic_registry

ROOT=Path(__file__).resolve().parents[1]
MARKER='data-v07-executive-overview="true"'
ANCHOR='<section class="panel" id="overview" aria-labelledby="tab-overview"><h2>概要</h2>'

EVENT_LABELS={
 "fomc-statement-2026-09":"FOMC政策声明",
 "fomc-press-conference-2026-09":"FOMC議長会見",
 "boj-policy-decision-2026-09":"日銀金融政策決定",
 "boj-governor-press-conference-2026-09":"日銀総裁会見",
}

def _status(event):
 state=event["outcome_state"]
 if state=="outcome_verified":return "結果確認済み","good"
 if state=="cancelled_verified":return "中止確認済み","pending"
 return "結果未確認","pending"

def _schedule(event):
 if event["scheduled_at"]:
  return event["scheduled_at"].replace("T"," ")
 return event["scheduled_date"]+" / 公表時刻は未確定"

def _registry_links(records,label_key):
 items=[]
 for record in records:
  suffix=''
  if record['kind']=='company':
   instrument=record['canonical_instrument']
   suffix=' <span class="small">'+escape(instrument['venue']+':'+instrument['symbol'])+'</span>'
  else:
   suffix=' <span class="small">'+escape(record['provider'])+'</span>'
  items.append('<a data-registry-'+label_key+'="'+escape(record['id'])+'" href="'+escape(record['source_url'],quote=True)+'" rel="noopener noreferrer" referrerpolicy="no-referrer">'+escape(record['name'])+'</a>'+suffix)
 return ' · '.join(items)

def _registry_block():
 meta=systemic_registry.validate()
 return (
  '<section data-systemic-registry="true" class="card full">'
  '<div class="eyebrow">FACT / SYSTEMIC IDENTITY REGISTRY</div>'
  '<h3>12指数 + 12発行体を共通IDで管理</h3>'
  '<div class="grid four">'
  '<article class="card"><div class="eyebrow">Indices</div><div class="metric">'+str(meta['index_count'])+'</div><p class="small">主要市場・地域の参照軸</p></article>'
  '<article class="card"><div class="eyebrow">Issuers</div><div class="metric">'+str(meta['company_count'])+'</div><p class="small">企業は発行体単位</p></article>'
  '<article class="card"><div class="eyebrow">Instruments</div><div class="metric">'+str(meta['instrument_count'])+'</div><p class="small">ADR・複数株式クラスを別管理</p></article>'
  '<article class="card"><div class="eyebrow">Verified</div><div class="metric">'+escape(meta['verified_at'])+'</div><p class="small">公式IR・指数提供者でidentity確認</p></article>'
  '</div>'
  '<div class="grid two">'
  '<article class="card"><div class="eyebrow">INDEX REGISTRY / FACT</div><p class="small">'+_registry_links(systemic_registry.INDEXES,'index')+'</p></article>'
  '<article class="card"><div class="eyebrow">ISSUER REGISTRY / FACT</div><p class="small">'+_registry_links(systemic_registry.COMPANIES,'company')+'</p></article>'
  '</div>'
  '<div class="notice"><strong>Deduplication rule:</strong> GOOGL/GOOG、TWSE:2330/NYSE:TSM、TSE:6857/ATEYYのような複数取引ラインは同一発行体IDへ束ねます。12社の選定はシステム波及を検証する初期アーキテクチャ用であり、投資ランキングではありません。</div>'
  '<p class="small">Registry scope: identity metadata only。株価、指数値、構成比、財務数値、バリュエーション、売買スコアはこのRegistryに保持しません。</p>'
  '</section>'
 )

def render(events=policy_events.EVENTS):
 policy_events.validate_events(events)
 systemic_registry.validate()
 verified=sum(e["outcome_state"]=="outcome_verified" for e in events)
 event_cards=[]
 for event in events:
  label,cls=_status(event)
  event_cards.append(
   '<article class="card" data-exec-event="'+escape(event["id"])+'">'
   '<div class="eyebrow">FACT / '+escape(event["authority"])+'</div>'
   '<h3>'+escape(EVENT_LABELS[event["id"]])+'</h3>'
   '<span class="tag '+cls+'">'+label+'</span>'
   '<p>'+escape(_schedule(event))+'</p>'
   '<p class="small">Outcome state: '+escape(event["outcome_state"])+' / '
   '<a href="'+escape(event["source_url"],quote=True)+'" rel="noopener noreferrer" referrerpolicy="no-referrer">公式出典</a></p>'
   '</article>'
  )
 systemic=(
  '<div class="grid">'
  '<article class="card"><div class="eyebrow">INFERENCE / TRANSMISSION</div><h3>Fed → 金利 → 株式</h3><p>FOMCの確認済み結果 → 米国債利回り → USD/JPY → Nasdaq-100・S&amp;P 500の順に反応の整合性を確認する。方向は事前固定しない。</p></article>'
  '<article class="card"><div class="eyebrow">INFERENCE / TRANSMISSION</div><h3>BOJ → 為替 → 日本株</h3><p>日銀の確認済み結果 → USD/JPY → TOPIX・日経225を確認する。政策決定の公表時刻は推測で補完しない。</p></article>'
  '<article class="card"><div class="eyebrow">INFERENCE / SYSTEMIC CHAIN</div><h3>AI需要 → 半導体 → 日本装置</h3><p>NVIDIA / Broadcom → TSMC / SK hynix → Advantest / Tokyo Electronを発行体IDで追跡し、企業名や上場ラインの重複を波及シグナルとして数えない。</p></article>'
  '<article class="card"><div class="eyebrow">INFERENCE / CROSS-THEME</div><h3>通信・資本コスト・宇宙</h3><p>NTT、MUFG、Rocket Labを異なる波及経路の観測点として扱う。Registryへの収録自体は投資魅力度を示さない。</p></article>'
  '</div>'
 )
 scenarios=(
  '<div class="grid">'
  '<article class="card"><div class="eyebrow">BULL / INFERENCE</div><h3>金融条件緩和が整合</h3><p>確認済み政策結果と金利・為替・株式の反応が緩和方向で整合する場合、成長株・リスク資産への追い風仮説を強める。</p></article>'
  '<article class="card"><div class="eyebrow">BASE / INFERENCE</div><h3>クロスアセット不一致</h3><p>政策結果は確認できても市場反応が分かれる場合、24時間のフォロースルーとイベント前レンジへの回帰を優先確認する。</p></article>'
  '<article class="card"><div class="eyebrow">BEAR / INFERENCE</div><h3>引締め方向が整合</h3><p>確認済み政策結果と金利・為替・株式が金融条件引締め方向で整合する場合、バリュエーション圧力とリスクオフを優先監視する。</p></article>'
  '</div>'
 )
 return (
  '<section '+MARKER+' class="card full">'
  '<div class="eyebrow">EXECUTIVE OVERVIEW / v0.7 PHASE 2</div>'
  '<h3>今日の判断レイヤー</h3>'
  '<div class="grid four">'
  '<article class="card"><div class="eyebrow">Typed policy events</div><div class="metric">'+str(len(events))+'</div><p class="small">FOMC / BOJ</p></article>'
  '<article class="card"><div class="eyebrow">Outcome verified</div><div class="metric">'+str(verified)+'</div><p class="small">時刻経過だけでは増えません</p></article>'
  '<article class="card"><div class="eyebrow">Claim discipline</div><div class="metric">FACT</div><p class="small">日程・identityは公式出典付き</p></article>'
  '<article class="card"><div class="eyebrow">Market direction</div><div class="metric">未判定</div><p class="small">外部Widget表示だけで方向を確定しません</p></article>'
  '</div>'
  '<div class="notice"><strong>What changed:</strong> 政策イベントに加え、主要指数・発行体を共通Registryへ統合しました。<br><strong>Why it matters:</strong> ADR、本国株、複数株式クラスの二重計上を防ぎ、次工程のイベント→指数→企業→テーマ接続を同一IDで構築できます。</div>'
  +_registry_block()+
  '<h3>最重要イベント</h3><div class="grid two">'+''.join(event_cards)+'</div>'
  '<h3>Systemic Market Map</h3>'+systemic+
  '<h3>Bull / Base / Bear</h3>'+scenarios+
  '<div class="notice"><strong>Invalidation / 反証:</strong> 24時間以内に金利・為替・株式がイベント前レンジへ戻る、または主要市場の反応が相互に矛盾する場合、政策イベント主導という仮説を弱めます。</div>'
  '<p class="small">Phase 2でも新規の自己ホスト株価、コンセンサス、企業スコア、売買推奨は追加していません。次工程ではRegistry IDへ evidence-backed relationship / catalyst recordsを接続します。</p>'
  '</section>'
 )

def apply(text:str,events=policy_events.EVENTS)->str:
 if MARKER in text:return text
 if ANCHOR not in text:raise ValueError("overview anchor missing")
 return text.replace(ANCHOR,ANCHOR+render(events),1)

def sync_manifest(site:Path,index_bytes:bytes)->None:
 path=site/'manifest.json';manifest=json.loads(path.read_text(encoding='utf-8'));files=manifest.get('files')
 if not isinstance(files,dict) or 'index.html' not in files:raise ValueError('manifest index entry')
 files['index.html']=hashlib.sha256(index_bytes).hexdigest()
 path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--path',default=str(ROOT/'site/index.html'));args=ap.parse_args()
 path=Path(args.path)
 text=path.read_text(encoding='utf-8')
 out=apply(text)
 if args.apply:
  encoded=out.encode('utf-8');path.write_bytes(encoded);sync_manifest(path.parent,encoded)
 else:print(out)

if __name__=='__main__':main()
