#!/usr/bin/env python3
"""Inject the v0.7 Executive Overview Phase 1 into the reviewed public HTML.

The panel is derived from typed policy-event records and adds no new market-data
transport or self-hosted quote payloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from html import escape
from pathlib import Path

import policy_events

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

def render(events=policy_events.EVENTS):
 policy_events.validate_events(events)
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
  '<article class="card"><div class="eyebrow">INFERENCE / TRANSMISSION</div><h3>Fed → 金利 → 株式</h3><p>FOMCの確認済み結果 → 米国債利回り → USD/JPY → NASDAQ・S&amp;P 500の順に反応の整合性を確認する。方向は事前固定しない。</p></article>'
  '<article class="card"><div class="eyebrow">INFERENCE / TRANSMISSION</div><h3>BOJ → 為替 → 日本株</h3><p>日銀の確認済み結果 → USD/JPY → TOPIX・日経225を確認する。政策決定の公表時刻は推測で補完しない。</p></article>'
  '<article class="card"><div class="eyebrow">INFERENCE / CROSS-ASSET</div><h3>日米政策差 → リスク選好</h3><p>金利差、為替、株式の同方向・逆方向を比較し、単一市場だけの初動を政策効果と断定しない。</p></article>'
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
  '<div class="eyebrow">EXECUTIVE OVERVIEW / v0.7 PHASE 1</div>'
  '<h3>今日の判断レイヤー</h3>'
  '<div class="grid four">'
  '<article class="card"><div class="eyebrow">Typed policy events</div><div class="metric">'+str(len(events))+'</div><p class="small">FOMC / BOJ</p></article>'
  '<article class="card"><div class="eyebrow">Outcome verified</div><div class="metric">'+str(verified)+'</div><p class="small">時刻経過だけでは増えません</p></article>'
  '<article class="card"><div class="eyebrow">Claim discipline</div><div class="metric">FACT</div><p class="small">日程・状態は公式出典付き</p></article>'
  '<article class="card"><div class="eyebrow">Market direction</div><div class="metric">未判定</div><p class="small">外部Widget表示だけで方向を確定しません</p></article>'
  '</div>'
  '<div class="notice"><strong>What changed:</strong> 重要政策イベントを、予定時刻ではなく結果確認状態で管理します。<br><strong>Why it matters:</strong> 未確認の発表を「通過済み」と誤認して投資判断へ使うリスクを下げます。</div>'
  '<h3>最重要イベント</h3><div class="grid two">'+''.join(event_cards)+'</div>'
  '<h3>Systemic Market Map</h3>'+systemic+
  '<h3>Bull / Base / Bear</h3>'+scenarios+
  '<div class="notice"><strong>Invalidation / 反証:</strong> 24時間以内に金利・為替・株式がイベント前レンジへ戻る、または主要市場の反応が相互に矛盾する場合、政策イベント主導という仮説を弱めます。</div>'
  '<p class="small">Phase 1では新規の自己ホスト株価、コンセンサス、企業スコア、売買推奨を追加していません。次工程で検証済みEntity / Index registryを接続します。</p>'
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
