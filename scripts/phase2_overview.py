#!/usr/bin/env python3
"""v0.7 Relevance Scoring Phase 2 + current-market presentation.

This final presentation transform removes reviewed 2026-09-10 archive prices from
the current overview, preserves the Executive Overview at runtime, and exposes
Relevance Scoring as research-attention metadata. Current market prices remain
provider-hosted TradingView data in the already-approved World / Stocks /
Policy-Reaction widgets; no quote values are stored or redistributed here.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from html import escape
from pathlib import Path

import company_theme_expansion
import executive_overview
import relationship_registry
import relevance_scoring

ROOT=Path(__file__).resolve().parents[1]
MARKER='data-relevance-scoring="true"'
PHASE4='EXECUTIVE OVERVIEW / v0.7 PHASE 4'
PHASE5='EXECUTIVE OVERVIEW / v0.7 PHASE 5'
INSERT_BEFORE='<section data-systemic-registry="true" class="card full">'

HOME_PRESERVE_OLD="const home=$('overview');empty(home);home.append(head);"
HOME_PRESERVE_NEW="const home=$('overview'),homeExecutive=home.querySelector('[data-v07-executive-overview]');empty(home);home.append(head);if(homeExecutive)home.append(homeExecutive);"
HOME_CAUTION_OLD="const caution=add(el('div','p-caution'),badge(J.past,'p-warn'),el('p','','価格の最終収録は '+D.as_of+'。一次情報の照合未完了で、現在の相場や売買シグナルではありません。'));"
HOME_CAUTION_NEW="const caution=add(el('div','p-caution'),badge('LIVE MARKET / PROVIDER-HOSTED','p-good'),el('p','','現在の株価・指数は「世界指数」「株価・決算」「イベント」のTradingView Widgetが閲覧時に配信します。取引所・契約条件によりリアルタイム、遅延、EODが混在し、当ビルドは表示価格を検証・保存しません。'));"
HOME_RIBBON_OLD="const ribbon=el('div','p-ribbon');for(const symbol of ['SPX','IXIC','N225','TOPIX','FTSE','KOSPI']){const a=MAP.get(symbol);const b=btn('',()=>go('world',symbol),'p-ticker');add(b,el('span','',names[symbol]),el('strong','',num(a.observations.at(-1).close)),el('small',ret(a)>=0?'rise':'fall',pct(ret(a))+' / 9.8 - 9.10'));ribbon.append(b);}home.append(ribbon);"
HOME_RIBBON_NEW="const ribbon=el('div','p-ribbon');for(const [label,target] of [['世界指数 LIVE','world'],['主要株・ETF LIVE','market'],['政策反応 LIVE','events']]){const b=btn(label,()=>go(target),'p-ticker');add(b,el('span','',label),el('strong','','Provider-hosted'),el('small','','閲覧時更新'));ribbon.append(b);}home.append(ribbon);"
HOME_KPI_OLD="const kpis=el('div','p-kpis');for(const [a,b,c] of [['14','世界の指数','4地域 / 3観測点'],['6','個別株・ETF','5社 + 1 ETF / 6取引日'],['8','登録イベント','予想・実績は未収録'],['6','マクロ自動取得系列','公的データ / 株価は対象外']])kpis.append(add(el('article','p-kpi'),el('small','',b),el('strong','',a),el('span','',c)));home.append(kpis);"
HOME_KPI_NEW="const kpis=el('div','p-kpis');for(const [a,b,c] of [['LIVE','Market feed','TradingView provider-hosted'],['21','Evidence relationships','3軸で調査優先度を管理'],['4','政策イベント','結果確認は一次情報後'],['0','自己ホスト current quotes','権利未承認のため使用禁止']])kpis.append(add(el('article','p-kpi'),el('small','',b),el('strong','',a),el('span','',c)));home.append(kpis);"
HOME_NEXT_OLD="add(next,btn('全8件の登録日程を確認',()=>go('events'),'p-link-button'),el('p','small','会合の未確認時刻を補完せず、時差を区別して表示します。'));cols.append(next);home.append(cols);"
HOME_NEXT_NEW="add(next,btn('登録日程とライブ反応を確認',()=>go('events'),'p-link-button'),el('p','small','現在値はprovider-hosted Widget、政策結果は一次資料確認後に判定します。'));cols.append(next);home.append(next);"
HOME_BOTTOM_OLD="add(bottom,leaders,plan);home.append(bottom);"
HOME_BOTTOM_NEW="home.append(plan);"
SCREENER_OLD="add(screen,el('div','p-eyebrow','COMPARE & SCREEN'),el('h2','',J.screen),el('p','p-lead','20系列を同じ日付で比較。色より、条件と根拠を確認します。'));"
SCREENER_NEW="add(screen,el('div','p-eyebrow','REVIEWED ARCHIVE / COMPARE & SCREEN'),el('h2','',J.screen),el('p','p-lead','監査用固定スナップショットの比較です。現在値・売買判断には使用せず、ライブ相場は「世界指数」「株価・決算」のTradingView表示を確認してください。'));"
RUNTIME_PAIRS=(
 (HOME_PRESERVE_OLD,HOME_PRESERVE_NEW),
 (HOME_CAUTION_OLD,HOME_CAUTION_NEW),
 (HOME_RIBBON_OLD,HOME_RIBBON_NEW),
 (HOME_KPI_OLD,HOME_KPI_NEW),
 (HOME_NEXT_OLD,HOME_NEXT_NEW),
 (HOME_BOTTOM_OLD,HOME_BOTTOM_NEW),
 (SCREENER_OLD,SCREENER_NEW),
)

ATTENTION_LABELS={
 'immediate':'IMMEDIATE / 今すぐ確認',
 'active':'ACTIVE / 継続監視',
 'watch':'WATCH / 次回確認',
 'structural':'STRUCTURAL / 中長期',
}


def _relationship_map():
 return {r['id']:r for r in relationship_registry.RELATIONSHIPS+company_theme_expansion.RELATIONSHIPS}


def _row(score):
 rel=_relationship_map()[score['relationship_id']]
 return (
  '<li data-relevance-score="'+escape(score['relationship_id'])+'" data-attention-state="'+escape(score['attention_state'])+'">'
  '<strong>'+escape(executive_overview._ref_name(rel['source_ref']))+' → '+escape(executive_overview._ref_name(rel['target_ref']))+'</strong> '
  '<span class="tag '+('pending' if score['attention_state']=='immediate' else 'good')+'">'+escape(ATTENTION_LABELS[score['attention_state']])+'</span><br>'
  '<span class="small">Market Impact '+str(score['market_impact'])+'/5 ・ Catalyst Urgency '+str(score['catalyst_urgency'])+'/5 ・ Evidence Strength '+str(score['evidence_strength'])+'/5<br>'
  'Basis: '+escape(score['rationale'])+'<br>Urgency basis: '+escape(score['urgency_basis'])+'</span></li>'
 )


def relevance_block():
 meta=relevance_scoring.validate();records=relevance_scoring.hydrated_records()
 groups={name:[r for r in records if r['attention_state']==name] for name in ('immediate','active','watch','structural')}
 return (
  '<section '+MARKER+' class="card full"><div class="eyebrow">RESEARCH ATTENTION / THREE INDEPENDENT AXES</div><h3>何を先に確認するかを21 Relationshipで管理</h3>'
  '<div class="grid four">'
  '<article class="card"><div class="eyebrow">Immediate</div><div class="metric">'+str(meta['immediate_count'])+'</div><p class="small">政策イベント等の即時確認</p></article>'
  '<article class="card"><div class="eyebrow">Active</div><div class="metric">'+str(meta['active_count'])+'</div><p class="small">AI需要・業績感応度等</p></article>'
  '<article class="card"><div class="eyebrow">Watch</div><div class="metric">'+str(meta['watch_count'])+'</div><p class="small">次回開示・実行状況</p></article>'
  '<article class="card"><div class="eyebrow">Structural</div><div class="metric">'+str(meta['structural_count'])+'</div><p class="small">中長期構造テーマ</p></article></div>'
  '<div class="notice"><strong>3軸は独立:</strong> Market Impact / Catalyst Urgency / Evidence Strengthを0–5で表示します。合計点、期待リターン、上昇確率、買い順位には変換しません。Immediateは一次資料を優先確認する対象であり、買いシグナルではありません。</div>'
  '<div class="grid two"><article class="card"><div class="eyebrow">IMMEDIATE</div><ul>'+''.join(_row(r) for r in groups['immediate'])+'</ul></article>'
  '<article class="card"><div class="eyebrow">ACTIVE</div><ul>'+''.join(_row(r) for r in groups['active'])+'</ul></article>'
  '<article class="card"><div class="eyebrow">WATCH</div><ul>'+''.join(_row(r) for r in groups['watch'])+'</ul></article>'
  '<article class="card"><div class="eyebrow">STRUCTURAL</div><ul>'+''.join(_row(r) for r in groups['structural'])+'</ul></article></div>'
  '<p class="small">Reviewed '+escape(meta['reviewed_at'])+' / research attention prioritization only / no combined score.</p></section>'
 )


def _restore_csp(text):
 scripts=re.findall(r'<script\b([^>]*)>(.*?)</script\s*>',text,re.I|re.S)
 inline=[body for attrs,body in scripts if 'src=' not in attrs.lower()]
 if len(inline)!=1:raise ValueError('inline script cardinality')
 digest=base64.b64encode(hashlib.sha256(inline[0].encode()).digest()).decode()
 pattern=r"script-src 'sha256-[^']+'"
 if len(re.findall(pattern,text))!=1:raise ValueError('csp cardinality')
 return re.sub(pattern,"script-src 'sha256-"+digest+"'",text,count=1)


def apply(text):
 if MARKER in text:return text
 if text.count(executive_overview.MARKER)!=1 or text.count(PHASE4)!=1 or text.count(INSERT_BEFORE)!=1:raise ValueError('phase2 anchor')
 for old,new in RUNTIME_PAIRS:
  if text.count(old)!=1 or new in text:raise ValueError('phase2 runtime source')
  text=text.replace(old,new,1)
 text=text.replace(PHASE4,PHASE5,1)
 text=text.replace(INSERT_BEFORE,relevance_block()+INSERT_BEFORE,1)
 return _restore_csp(text)


def sync_manifest(site,index_bytes):
 path=site/'manifest.json';manifest=json.loads(path.read_text(encoding='utf-8'));files=manifest.get('files')
 if not isinstance(files,dict) or 'index.html' not in files:raise ValueError('manifest index')
 files['index.html']=hashlib.sha256(index_bytes).hexdigest();path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--path',default=str(ROOT/'site/index.html'));args=ap.parse_args();path=Path(args.path);out=apply(path.read_text(encoding='utf-8'))
 if args.apply:
  data=out.encode();path.write_bytes(data);sync_manifest(path.parent,data)
 else:print(out)

if __name__=='__main__':main()
