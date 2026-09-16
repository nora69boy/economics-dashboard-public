#!/usr/bin/env python3
"""Inject the v0.7 Executive Overview into the reviewed public HTML.

The panel is derived from typed policy events, the reviewed identity-only systemic
registry, the evidence-backed relationship/catalyst registry, and the reviewed
company/theme expansion. It adds no new market-data transport or self-hosted
quote payloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from html import escape
from pathlib import Path

import company_theme_expansion
import policy_events
import relationship_registry
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
CATALYST_LABELS={
 "catalyst-fomc-2026-09":"FOMC → 金利・ドル・米国株",
 "catalyst-boj-2026-09":"BOJ → 金利・USD/JPY・日本株",
 "catalyst-ai-semi-demand-2026q3":"AI需要 → 半導体供給網・装置",
}
MONITOR_LABELS={
 "monitor-hyperscaler-ai-capacity-2026h2":"Hyperscaler AI capacity",
 "monitor-ai-networking-broadcom-2026h2":"AI accelerators / networking",
 "monitor-jp-rate-mufg-fy26":"Japan rates → MUFG earnings sensitivity",
 "monitor-photonics-ai-infra-2026-27":"Photonics / AIOWN commercialization",
 "monitor-space-launch-systems-2026":"Launch / space systems execution",
}

def _status(event):
 state=event["outcome_state"]
 if state=="outcome_verified":return "結果確認済み","good"
 if state=="cancelled_verified":return "中止確認済み","pending"
 return "結果未確認","pending"

def _schedule(event):
 if event["scheduled_at"]:return event["scheduled_at"].replace("T"," ")
 return event["scheduled_date"]+" / 公表時刻は未確定"

def _registry_links(records,label_key):
 items=[]
 for record in records:
  if record['kind']=='company':
   instrument=record['canonical_instrument'];suffix=' <span class="small">'+escape(instrument['venue']+':'+instrument['symbol'])+'</span>'
  else:suffix=' <span class="small">'+escape(record['provider'])+'</span>'
  items.append('<a data-registry-'+label_key+'="'+escape(record['id'])+'" href="'+escape(record['source_url'],quote=True)+'" rel="noopener noreferrer" referrerpolicy="no-referrer">'+escape(record['name'])+'</a>'+suffix)
 return ' · '.join(items)

def _registry_block():
 meta=systemic_registry.validate()
 return (
  '<section data-systemic-registry="true" class="card full">'
  '<div class="eyebrow">FACT / SYSTEMIC IDENTITY REGISTRY</div><h3>12指数 + 12発行体を共通IDで管理</h3>'
  '<div class="grid four">'
  '<article class="card"><div class="eyebrow">Indices</div><div class="metric">'+str(meta['index_count'])+'</div><p class="small">主要市場・地域の参照軸</p></article>'
  '<article class="card"><div class="eyebrow">Issuers</div><div class="metric">'+str(meta['company_count'])+'</div><p class="small">企業は発行体単位</p></article>'
  '<article class="card"><div class="eyebrow">Instruments</div><div class="metric">'+str(meta['instrument_count'])+'</div><p class="small">ADR・複数株式クラスを別管理</p></article>'
  '<article class="card"><div class="eyebrow">Verified</div><div class="metric">'+escape(meta['verified_at'])+'</div><p class="small">公式IR・指数提供者でidentity確認</p></article>'
  '</div><div class="grid two">'
  '<article class="card"><div class="eyebrow">INDEX REGISTRY / FACT</div><p class="small">'+_registry_links(systemic_registry.INDEXES,'index')+'</p></article>'
  '<article class="card"><div class="eyebrow">ISSUER REGISTRY / FACT</div><p class="small">'+_registry_links(systemic_registry.COMPANIES,'company')+'</p></article>'
  '</div>'
  '<div class="notice"><strong>Deduplication rule:</strong> GOOGL/GOOG、TWSE:2330/NYSE:TSM、TSE:6857/ATEYYのような複数取引ラインは同一発行体IDへ束ねます。12社の選定はシステム波及を検証する初期アーキテクチャ用であり、投資ランキングではありません。</div>'
  '<p class="small">Registry scope: identity metadata only。株価、指数値、構成比、財務数値、バリュエーション、売買スコアはこのRegistryに保持しません。</p></section>'
 )

def _ref_name(ref):
 kind,ident=ref.split(':',1)
 if kind=='event':return EVENT_LABELS.get(ident,ident)
 if kind=='index':return systemic_registry.by_id(ident)['name']
 if kind=='company':return systemic_registry.by_id(ident)['name']
 if kind=='factor':
  match=[x for x in relationship_registry.FACTORS if x['id']==ident]
 elif kind=='theme':
  match=[x for x in relationship_registry.THEMES+company_theme_expansion.THEMES if x['id']==ident]
 else:match=[]
 if len(match)!=1:raise KeyError(ref)
 return match[0]['name']

def _relationship_row(rel):
 state='確認が必要' if rel['publication_state']=='confirm_required' else rel['claim_type']
 published=rel['source_published_at'] or '公表日記載なし'
 return (
  '<li data-relationship="'+escape(rel['id'])+'"><strong>'+escape(_ref_name(rel['source_ref']))+' → '+escape(_ref_name(rel['target_ref']))+'</strong> '
  '<span class="tag '+('pending' if rel['publication_state']=='confirm_required' else 'good')+'">'+escape(state)+'</span>'
  '<br><span class="small">'+escape(rel['claim'])+' / Evidence '+escape(rel['evidence_grade'])+' / source published: '+escape(published)+' / verified: '+escape(rel['verified_at'])+' / '
  '<a href="'+escape(rel['source_url'],quote=True)+'" rel="noopener noreferrer" referrerpolicy="no-referrer">一次出典</a><br><strong>Invalidation:</strong> '+escape(rel['invalidation'])+'</span></li>'
 )

def _expansion_row(rel):
 return (
  '<li data-company-theme-relationship="'+escape(rel['id'])+'"><strong>'+escape(_ref_name(rel['source_ref']))+' → '+escape(_ref_name(rel['target_ref']))+'</strong> '
  '<span class="tag good">FACT</span><br><span class="small">'+escape(rel['claim'])+' / Evidence '+escape(rel['evidence_grade'])+' / source published: '+escape(rel['source_published_at'])+' / verified: '+escape(rel['verified_at'])+' / '
  '<a href="'+escape(rel['source_url'],quote=True)+'" rel="noopener noreferrer" referrerpolicy="no-referrer">一次出典</a><br><strong>Invalidation:</strong> '+escape(rel['invalidation'])+'</span></li>'
 )

def _monitor_card(monitor):
 return (
  '<article class="card" data-company-theme-monitor="'+escape(monitor['id'])+'"><div class="eyebrow">MONITOR / INFERENCE</div><h3>'+escape(MONITOR_LABELS[monitor['id']])+'</h3>'
  '<span class="tag good">構造監視中</span><p class="small">Monitor: '+escape(monitor['monitor_window'])+'<br>Activation: '+escape(monitor['activation_rule'])+'<br><strong>Invalidation:</strong> '+escape(monitor['invalidation'])+'</p></article>'
 )

def _company_theme_block():
 meta=company_theme_expansion.validate()
 ai_ids={'rel-ai-cloud-microsoft','rel-ai-cloud-alphabet','rel-ai-cloud-amazon','rel-ai-networking-broadcom'}
 ai=[r for r in company_theme_expansion.RELATIONSHIPS if r['id'] in ai_ids]
 strategic=[r for r in company_theme_expansion.RELATIONSHIPS if r['id'] not in ai_ids]
 return (
  '<section data-company-theme-expansion="true" class="card full"><div class="eyebrow">FACT + INFERENCE / COMPANY &amp; THEME EXPANSION</div><h3>12/12 seed issuers をEvidence Graphへ接続</h3>'
  '<div class="grid four">'
  '<article class="card"><div class="eyebrow">Seed coverage</div><div class="metric">'+str(meta['seed_company_coverage'])+'/12</div><p class="small">全初期発行体に証拠付き接続</p></article>'
  '<article class="card"><div class="eyebrow">Expansion FACT</div><div class="metric">'+str(meta['relationship_count'])+'</div><p class="small">Grade A一次資料</p></article>'
  '<article class="card"><div class="eyebrow">Themes</div><div class="metric">'+str(meta['theme_count'])+'</div><p class="small">AI cloud / networking / photonics / space</p></article>'
  '<article class="card"><div class="eyebrow">Monitors</div><div class="metric">'+str(meta['monitor_count'])+'</div><p class="small">INFERENCE + 反証条件</p></article></div>'
  '<div class="grid">'+''.join(_monitor_card(m) for m in company_theme_expansion.MONITORS)+'</div>'
  '<div class="grid two"><article class="card"><div class="eyebrow">AI CLOUD / NETWORKING</div><ul>'+''.join(_expansion_row(r) for r in ai)+'</ul></article>'
  '<article class="card"><div class="eyebrow">JAPAN RATES / PHOTONICS / SPACE</div><ul>'+''.join(_expansion_row(r) for r in strategic)+'</ul></article></div>'
  '<div class="notice"><strong>Coverage rule:</strong> 12/12は投資評価ではなく、初期発行体すべてに少なくとも1本のevidence-backed relationshipがあることを示します。MONITORは売買シグナルではなく、次回公式開示で維持・弱化・退役を判断する検証レイヤーです。</div></section>'
 )

def _catalyst_label(state):
 return {
  'pending_outcome_verification':('結果確認待ち','pending'),
  'outcome_verified_monitoring':('結果確認済み / 監視中','good'),
  'cancelled_verified':('中止確認済み','pending'),
  'monitoring':('構造監視中','good'),
 }[state]

def _relationship_block(events):
 meta=relationship_registry.validate();cards=[]
 for catalyst in relationship_registry.CATALYSTS:
  state=relationship_registry.catalyst_state(catalyst,events);label,cls=_catalyst_label(state)
  cards.append('<article class="card" data-catalyst="'+escape(catalyst['id'])+'"><div class="eyebrow">CATALYST / INFERENCE</div><h3>'+escape(CATALYST_LABELS[catalyst['id']])+'</h3><span class="tag '+cls+'">'+label+'</span><p class="small">Monitor: '+escape(catalyst['monitor_window'])+'<br>Activation: '+escape(catalyst['activation_rule'])+'<br><strong>Invalidation:</strong> '+escape(catalyst['invalidation'])+'</p></article>')
 policy_ids={'rel-fomc-policy-rate','rel-us-rate-financial-conditions','rel-us-financial-sp500','rel-us-financial-nasdaq100','rel-fomc-usd-channel','rel-boj-policy-rate','rel-boj-usdjpy','rel-usdjpy-topix'}
 policy=[r for r in relationship_registry.RELATIONSHIPS if r['id'] in policy_ids];ai=[r for r in relationship_registry.RELATIONSHIPS if r['id'] not in policy_ids]
 return (
  '<section data-relationship-registry="true" class="card full"><div class="eyebrow">FACT + INFERENCE / RELATIONSHIP REGISTRY</div><h3>Event → Macro → Index → Issuer の根拠付き接続</h3>'
  '<div class="grid four">'
  '<article class="card"><div class="eyebrow">Relationships</div><div class="metric">'+str(meta['relationship_count'])+'</div><p class="small">重複ID禁止</p></article>'
  '<article class="card"><div class="eyebrow">FACT</div><div class="metric">'+str(meta['fact_count'])+'</div><p class="small">Grade A一次資料必須</p></article>'
  '<article class="card"><div class="eyebrow">INFERENCE</div><div class="metric">'+str(meta['inference_count'])+'</div><p class="small">反証条件必須</p></article>'
  '<article class="card"><div class="eyebrow">確認が必要</div><div class="metric">'+str(meta['confirm_required_count'])+'</div><p class="small">未解決FACTは公開不可</p></article></div>'
  '<div class="grid">'+''.join(cards)+'</div>'
  '<div class="grid two"><article class="card"><div class="eyebrow">POLICY TRANSMISSION</div><ul>'+''.join(_relationship_row(r) for r in policy)+'</ul></article>'
  '<article class="card"><div class="eyebrow">AI / SEMICONDUCTOR TRANSMISSION</div><ul>'+''.join(_relationship_row(r) for r in ai)+'</ul></article></div>'
  '<div class="notice"><strong>Interpretation rule:</strong> Relationshipは因果を自動認定しません。直接開示された供給関係・需要接続だけをFACTとし、市場波及はINFERENCEとして反証条件を保持します。未確認項目は「確認が必要」に降格します。</div></section>'
 )

def _chain(ids):
 rels=[relationship_registry.by_id(i) for i in ids]
 names=[_ref_name(rels[0]['source_ref'])]+[_ref_name(r['target_ref']) for r in rels]
 return ' → '.join(escape(x) for x in names)

def render(events=policy_events.EVENTS):
 policy_events.validate_events(events);systemic_registry.validate();relationship_registry.validate();company_theme_expansion.validate()
 verified=sum(e["outcome_state"]=="outcome_verified" for e in events);event_cards=[]
 for event in events:
  label,cls=_status(event)
  event_cards.append('<article class="card" data-exec-event="'+escape(event["id"])+'"><div class="eyebrow">FACT / '+escape(event["authority"])+'</div><h3>'+escape(EVENT_LABELS[event["id"]])+'</h3><span class="tag '+cls+'">'+label+'</span><p>'+escape(_schedule(event))+'</p><p class="small">Outcome state: '+escape(event["outcome_state"])+' / <a href="'+escape(event["source_url"],quote=True)+'" rel="noopener noreferrer" referrerpolicy="no-referrer">公式出典</a></p></article>')
 systemic=(
  '<div class="grid">'
  '<article class="card"><div class="eyebrow">EVIDENCE CHAIN</div><h3>Fed → 金融条件 → 市場</h3><p>'+_chain(('rel-fomc-policy-rate','rel-us-rate-financial-conditions'))+'。S&amp;P 500 / Nasdaq-100への波及はINFERENCEとして別管理し、方向は事前固定しない。</p></article>'
  '<article class="card"><div class="eyebrow">EVIDENCE CHAIN</div><h3>BOJ → 為替 → 日本株</h3><p>'+_chain(('rel-boj-policy-rate','rel-boj-usdjpy','rel-usdjpy-topix'))+'。政策決定の公表時刻は推測で補完しない。</p></article>'
  '<article class="card"><div class="eyebrow">EVIDENCE CHAIN</div><h3>AI需要 → 半導体・装置</h3><p>AI/HPC/HBM需要 → TSMC / SK hynix / Advantest / Tokyo Electronを一次資料で追跡。NVIDIA → TSMC / SK hynixは2026年10-Kの直接開示をFACTとして保持。</p></article>'
  '<article class="card"><div class="eyebrow">EVIDENCE CHAIN</div><h3>AI cloud → Hyperscalers / Networking</h3><p>AI cloud / datacenter infrastructure → Microsoft / Alphabet / Amazon、custom AI accelerators / networking → Broadcomを一次資料で追跡。</p></article>'
  '<article class="card"><div class="eyebrow">EVIDENCE CHAIN</div><h3>Japan rates / Photonics</h3><p>日本政策金利 → MUFGの利息収益感応度、photonics-enabled AI infrastructure → NTTのAIOWN / APN戦略をFACTとして追跡。</p></article>'
  '<article class="card"><div class="eyebrow">EVIDENCE CHAIN</div><h3>Space infrastructure</h3><p>Launch services / space systems demand → Rocket Lab。契約・backlog・launch executionを分離し、backlogだけで株価方向を推定しない。</p></article>'
  '</div>'
 )
 scenarios=(
  '<div class="grid">'
  '<article class="card"><div class="eyebrow">BULL / INFERENCE</div><h3>金融条件・AI需要・設備投資が整合</h3><p>確認済み政策結果と市場反応が緩和方向で整合し、AI半導体・cloud capacity・networkingの一次資料でも需要継続が確認される場合、成長資産への追い風仮説を強める。MUFG・NTT・Rocket Labは各社固有の反証条件を別管理する。</p></article>'
  '<article class="card"><div class="eyebrow">BASE / INFERENCE</div><h3>テーマは継続、企業間の強弱は分岐</h3><p>政策・AI需要の方向は維持しても企業ごとのcapacity、margin、rate sensitivity、commercialization、executionに差が出る場合、テーマ全体ではなくRelationship単位で維持・弱化を判定する。</p></article>'
  '<article class="card"><div class="eyebrow">BEAR / INFERENCE</div><h3>金融条件引締め / AI投資鈍化 / 実行遅延</h3><p>政策結果と金利・為替・株式が引締め方向で整合、AI/cloud投資計画が縮小、またはNTT/Rocket Labなどの固有マイルストーンが後退する場合、該当RelationshipとMonitorを弱化・退役させる。</p></article>'
  '</div>'
 )
 total_relationships=len(relationship_registry.RELATIONSHIPS)+len(company_theme_expansion.RELATIONSHIPS)
 return (
  '<section '+MARKER+' class="card full"><div class="eyebrow">EXECUTIVE OVERVIEW / v0.7 PHASE 4</div><h3>今日の判断レイヤー</h3>'
  '<div class="grid four">'
  '<article class="card"><div class="eyebrow">Typed policy events</div><div class="metric">'+str(len(events))+'</div><p class="small">FOMC / BOJ</p></article>'
  '<article class="card"><div class="eyebrow">Outcome verified</div><div class="metric">'+str(verified)+'</div><p class="small">時刻経過だけでは増えません</p></article>'
  '<article class="card"><div class="eyebrow">Evidence relationships</div><div class="metric">'+str(total_relationships)+'</div><p class="small">14 base + 7 company/theme</p></article>'
  '<article class="card"><div class="eyebrow">Issuer coverage</div><div class="metric">12/12</div><p class="small">coverage ≠ ranking</p></article></div>'
  '<div class="notice"><strong>What changed:</strong> Company / Theme ExpansionをExecutive Overviewへ接続し、初期12発行体すべてをEvidence Graph上で可視化しました。<br><strong>Why it matters:</strong> AI cloud・networking・日本金利・photonics・spaceを、一次資料FACTと反証可能なMonitorに分けて追跡できます。</div>'
  +_registry_block()+_relationship_block(events)+_company_theme_block()+
  '<h3>最重要イベント</h3><div class="grid two">'+''.join(event_cards)+'</div><h3>Systemic Market Map</h3>'+systemic+
  '<h3>Bull / Base / Bear</h3>'+scenarios+
  '<div class="notice"><strong>Invalidation / 反証:</strong> 政策波及は24時間以内のフォロースルーがなくイベント前レンジへ回帰した場合に弱化。企業・テーマは後続の公式決算・filing・事業進捗が現在の需要接続、金利感応度、commercialization、execution前提を反転させた場合に該当Relationship / Monitorを弱化・退役します。</div>'
  '<p class="small">Phase 4でも新規の自己ホスト株価、コンセンサス、企業スコア、確率、売買推奨は追加していません。12/12 coverageは投資ランキングではありません。</p></section>'
 )

def apply(text:str,events=policy_events.EVENTS)->str:
 if MARKER in text:return text
 if ANCHOR not in text:raise ValueError("overview anchor missing")
 return text.replace(ANCHOR,ANCHOR+render(events),1)

def sync_manifest(site:Path,index_bytes:bytes)->None:
 path=site/'manifest.json';manifest=json.loads(path.read_text(encoding='utf-8'));files=manifest.get('files')
 if not isinstance(files,dict) or 'index.html' not in files:raise ValueError('manifest index entry')
 files['index.html']=hashlib.sha256(index_bytes).hexdigest();path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--path',default=str(ROOT/'site/index.html'));args=ap.parse_args();path=Path(args.path);text=path.read_text(encoding='utf-8');out=apply(text)
 if args.apply:
  encoded=out.encode('utf-8');path.write_bytes(encoded);sync_manifest(path.parent,encoded)
 else:print(out)

if __name__=='__main__':main()
