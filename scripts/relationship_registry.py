#!/usr/bin/env python3
"""Evidence-backed v0.7 Relationship / Catalyst Registry Phase 1.

This registry connects reviewed policy events, macro factors, systemic indices,
issuer IDs, and the initial AI-semiconductor theme. It is deliberately qualitative:
no price targets, probabilities, buy scores, recommendations, or portfolio sizing.
FACT records require primary-source evidence. INFERENCE records remain explicitly
analytical and require an invalidation condition.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

import policy_events
import systemic_registry

SCHEMA_VERSION="0.7-relationship1"
VERIFIED_AT="2026-09-16"
PUBLICATION_SCOPE="evidence_backed_relationships_only"
ALLOWED_CLAIMS={"FACT","INFERENCE"}
ALLOWED_GRADES={"A","B","C"}
ALLOWED_STATES={"publishable","confirm_required"}
ALLOWED_RELATION_TYPES={
 "policy_transmission","market_transmission","demand_exposure",
 "manufacturing_dependency","memory_supply_dependency"
}

FACTORS=(
 {"id":"factor-us-policy-rate","kind":"macro_factor","name":"U.S. policy rate / expected path"},
 {"id":"factor-us-financial-conditions","kind":"macro_factor","name":"U.S. financial conditions"},
 {"id":"factor-usd","kind":"macro_factor","name":"U.S. dollar / FX channel"},
 {"id":"factor-jp-policy-rate","kind":"macro_factor","name":"Japan policy rate / expected path"},
 {"id":"factor-usdjpy","kind":"macro_factor","name":"USD/JPY transmission channel"},
)

THEMES=(
 {"id":"theme-ai-compute-demand","kind":"theme","name":"AI accelerator / HPC semiconductor demand"},
)

RELATIONSHIPS=(
 {"id":"rel-fomc-policy-rate","source_ref":"event:fomc-statement-2026-09","target_ref":"factor:factor-us-policy-rate","relation_type":"policy_transmission","claim_type":"FACT","evidence_grade":"A","claim":"FOMC policy decisions set the target range for the federal funds rate and initiate transmission through other financial conditions.","source_url":"https://www.federalreserve.gov/fomc/","source_title":"Federal Open Market Committee","source_date":"2026-09-16","verified_at":VERIFIED_AT,"invalidation":"Federal Reserve documentation no longer identifies the FOMC as setting the federal funds target range.","publication_state":"publishable"},
 {"id":"rel-us-rate-financial-conditions","source_ref":"factor:factor-us-policy-rate","target_ref":"factor:factor-us-financial-conditions","relation_type":"policy_transmission","claim_type":"FACT","evidence_grade":"A","claim":"Changes in the federal funds target and expected path affect longer-term rates, asset prices and broader financial conditions.","source_url":"https://www.federalreserve.gov/monetarypolicy/monetary-policy-what-are-its-goals-how-does-it-work.htm","source_title":"Monetary Policy: What Are Its Goals? How Does It Work?","source_date":"2026-03-01","verified_at":VERIFIED_AT,"invalidation":"Federal Reserve transmission guidance materially changes this channel description.","publication_state":"publishable"},
 {"id":"rel-us-financial-sp500","source_ref":"factor:factor-us-financial-conditions","target_ref":"index:index-sp500","relation_type":"market_transmission","claim_type":"INFERENCE","evidence_grade":"B","claim":"Use the S&P 500 as a broad-equity observation point for whether U.S. policy-driven financial-condition changes transmit into equities; do not infer direction before the market response is observed.","source_url":"https://www.federalreserve.gov/monetarypolicy/monetary-policy-what-are-its-goals-how-does-it-work.htm","source_title":"Monetary Policy: What Are Its Goals? How Does It Work?","source_date":"2026-03-01","verified_at":VERIFIED_AT,"invalidation":"The index returns to its pre-event range within 24 hours or diverges from the broader rates/FX transmission signal.","publication_state":"publishable"},
 {"id":"rel-us-financial-nasdaq100","source_ref":"factor:factor-us-financial-conditions","target_ref":"index:index-nasdaq100","relation_type":"market_transmission","claim_type":"INFERENCE","evidence_grade":"B","claim":"Use the Nasdaq-100 as a growth-equity observation point for policy-driven financial-condition transmission; direction remains an observed outcome, not a pre-event assumption.","source_url":"https://www.federalreserve.gov/monetarypolicy/monetary-policy-what-are-its-goals-how-does-it-work.htm","source_title":"Monetary Policy: What Are Its Goals? How Does It Work?","source_date":"2026-03-01","verified_at":VERIFIED_AT,"invalidation":"The index shows no follow-through or reverses to the pre-event range within 24 hours while rates/FX move in the opposite direction.","publication_state":"publishable"},
 {"id":"rel-fomc-usd-channel","source_ref":"factor:factor-us-financial-conditions","target_ref":"factor:factor-usd","relation_type":"market_transmission","claim_type":"FACT","evidence_grade":"A","claim":"Federal Reserve guidance identifies exchange rates as one channel through which U.S. interest-rate changes transmit to the economy.","source_url":"https://www.federalreserve.gov/monetarypolicy/monetary-policy-what-are-its-goals-how-does-it-work.htm","source_title":"Monetary Policy: What Are Its Goals? How Does It Work?","source_date":"2026-03-01","verified_at":VERIFIED_AT,"invalidation":"Federal Reserve transmission guidance materially removes or reverses the exchange-rate channel description.","publication_state":"publishable"},
 {"id":"rel-boj-policy-rate","source_ref":"event:boj-policy-decision-2026-09","target_ref":"factor:factor-jp-policy-rate","relation_type":"policy_transmission","claim_type":"FACT","evidence_grade":"A","claim":"The Bank of Japan Policy Board decides the monetary-policy stance at Monetary Policy Meetings and implements policy by influencing interest-rate formation.","source_url":"https://www.boj.or.jp/en/mopo/outline/","source_title":"Outline of Monetary Policy","source_date":"2026-09-16","verified_at":VERIFIED_AT,"invalidation":"Bank of Japan documentation materially changes the decision or implementation framework.","publication_state":"publishable"},
 {"id":"rel-boj-usdjpy","source_ref":"factor:factor-jp-policy-rate","target_ref":"factor:factor-usdjpy","relation_type":"market_transmission","claim_type":"INFERENCE","evidence_grade":"B","claim":"Monitor USD/JPY as a transmission channel around BOJ policy changes because interest-rate differentials can affect foreign-exchange rates, but do not assume a deterministic direction.","source_url":"https://www.boj.or.jp/en/about/press/koen_2021/ko211223a.htm","source_title":"Monetary Policy and Firms' Behavior: Foreign Exchange Rate Channel","source_date":"2021-12-23","verified_at":VERIFIED_AT,"invalidation":"USD/JPY fails to show event-window follow-through or moves primarily on a clearly identified non-BOJ catalyst.","publication_state":"publishable"},
 {"id":"rel-usdjpy-topix","source_ref":"factor:factor-usdjpy","target_ref":"index:index-topix","relation_type":"market_transmission","claim_type":"INFERENCE","evidence_grade":"B","claim":"Use TOPIX as a Japan-equity observation point for whether BOJ/FX transmission broadens into domestic equities; do not treat FX direction alone as sufficient evidence.","source_url":"https://www.boj.or.jp/en/about/press/koen_2026/ko260827a.htm","source_title":"Japan's Economy and Monetary Policy","source_date":"2026-08-27","verified_at":VERIFIED_AT,"invalidation":"TOPIX returns to its pre-event range within 24 hours or sector breadth contradicts an FX-led market interpretation.","publication_state":"publishable"},
 {"id":"rel-ai-demand-tsmc","source_ref":"theme:theme-ai-compute-demand","target_ref":"company:company-tsmc","relation_type":"demand_exposure","claim_type":"FACT","evidence_grade":"A","claim":"TSMC reports robust AI-related demand and says increasing AI adoption supports demand for leading-edge silicon and HPC-related advanced technologies.","source_url":"https://investor.tsmc.com/static/annualReports/2025/english/index.html","source_title":"TSMC 2025 Annual Report","source_date":"2026-04-17","verified_at":VERIFIED_AT,"invalidation":"A later TSMC filing materially weakens or reverses the stated AI/HPC demand linkage.","publication_state":"publishable"},
 {"id":"rel-ai-demand-skhynix","source_ref":"theme:theme-ai-compute-demand","target_ref":"company:company-skhynix","relation_type":"demand_exposure","claim_type":"FACT","evidence_grade":"A","claim":"SK hynix reports strong AI memory demand as a driver of high-value DRAM/HBM product sales and capacity planning.","source_url":"https://news.skhynix.com/en/q2-2026-business-results/","source_title":"SK hynix 2Q26 Financial Results","source_date":"2026-07-29","verified_at":VERIFIED_AT,"invalidation":"A later SK hynix results release materially weakens or reverses the stated AI/HBM demand linkage.","publication_state":"publishable"},
 {"id":"rel-ai-demand-advantest","source_ref":"theme:theme-ai-compute-demand","target_ref":"company:company-advantest","relation_type":"demand_exposure","claim_type":"FACT","evidence_grade":"A","claim":"Advantest reports that rising production volumes and complexity of AI/HPC semiconductors are increasing tester demand.","source_url":"https://www.advantest.com/en/investors/financial-highlights/forecast/","source_title":"Advantest Earnings Forecast","source_date":"2026-07-30","verified_at":VERIFIED_AT,"invalidation":"A later Advantest outlook no longer identifies AI/HPC semiconductor volume or complexity as a material tester-demand driver.","publication_state":"publishable"},
 {"id":"rel-ai-demand-tel","source_ref":"theme:theme-ai-compute-demand","target_ref":"company:company-tokyo-electron","relation_type":"demand_exposure","claim_type":"FACT","evidence_grade":"A","claim":"Tokyo Electron identifies leading-edge logic and HBM for AI servers as growth drivers and reports strong advanced-packaging inquiries for HBM applications.","source_url":"https://www.tel.com/ir/library/report/pjuomj00000000tf-att/FY26Q4_EarningCall_QA_E.pdf","source_title":"Tokyo Electron Q4 FY2026 Earnings Briefing Q&A","source_date":"2026-05-12","verified_at":VERIFIED_AT,"invalidation":"A later Tokyo Electron outlook materially weakens the AI-server/HBM equipment-demand linkage.","publication_state":"publishable"},
 {"id":"rel-nvidia-tsmc","source_ref":"company:company-nvidia","target_ref":"company:company-tsmc","relation_type":"manufacturing_dependency","claim_type":"FACT","evidence_grade":"A","claim":"NVIDIA identifies TSMC as one of the foundries it uses to produce semiconductor wafers.","source_url":"https://investor.nvidia.com/financial-info/sec-filings/sec-filings-details/default.aspx?FilingId=19184805","source_title":"NVIDIA Form 10-K filed February 25, 2026","source_date":"2026-02-25","verified_at":VERIFIED_AT,"invalidation":"A later NVIDIA filing no longer identifies TSMC as a wafer foundry or materially changes the manufacturing model.","publication_state":"publishable"},
 {"id":"rel-nvidia-skhynix","source_ref":"company:company-nvidia","target_ref":"company:company-skhynix","relation_type":"memory_supply_dependency","claim_type":"FACT","evidence_grade":"A","claim":"NVIDIA identifies SK hynix among the suppliers from which it purchases memory.","source_url":"https://investor.nvidia.com/financial-info/sec-filings/sec-filings-details/default.aspx?FilingId=19184805","source_title":"NVIDIA Form 10-K filed February 25, 2026","source_date":"2026-02-25","verified_at":VERIFIED_AT,"invalidation":"A later NVIDIA filing no longer identifies SK hynix as a memory supplier or materially changes the disclosed sourcing model.","publication_state":"publishable"},
)

CATALYSTS=(
 {"id":"catalyst-fomc-2026-09","kind":"scheduled_policy_event","trigger_event_ref":"event:fomc-statement-2026-09","relationship_ids":("rel-fomc-policy-rate","rel-us-rate-financial-conditions","rel-us-financial-sp500","rel-us-financial-nasdaq100","rel-fomc-usd-channel"),"monitor_window":"0-24h after verified outcome","activation_rule":"Only a source-verified FOMC outcome activates post-event interpretation; clock passage alone does not.","invalidation":"No coherent follow-through across rates, USD and broad/growth equities within 24 hours.","claim_type":"INFERENCE"},
 {"id":"catalyst-boj-2026-09","kind":"scheduled_policy_event","trigger_event_ref":"event:boj-policy-decision-2026-09","relationship_ids":("rel-boj-policy-rate","rel-boj-usdjpy","rel-usdjpy-topix"),"monitor_window":"0-24h after verified outcome","activation_rule":"Only a source-verified BOJ decision activates post-event interpretation; the unknown publication time is not invented.","invalidation":"No coherent follow-through across Japanese rates/FX/equity breadth or a clearly stronger non-BOJ catalyst dominates.","claim_type":"INFERENCE"},
 {"id":"catalyst-ai-semi-demand-2026q3","kind":"structural_monitor","trigger_event_ref":None,"relationship_ids":("rel-ai-demand-tsmc","rel-ai-demand-skhynix","rel-ai-demand-advantest","rel-ai-demand-tel","rel-nvidia-tsmc","rel-nvidia-skhynix"),"monitor_window":"through next issuer earnings cycle","activation_rule":"Maintain the chain only while current primary-source disclosures continue to support AI/HPC/HBM demand and the disclosed supplier relationships.","invalidation":"One or more later primary filings materially reverse the demand linkage or supplier relationship; affected links must then be downgraded or retired.","claim_type":"INFERENCE"},
)

FORBIDDEN_KEYS={"price","target_price","probability","buy_score","score","recommendation","position_size","ranking"}

def _walk_keys(value):
 if isinstance(value,dict):
  for key,item in value.items():
   yield key
   yield from _walk_keys(item)
 elif isinstance(value,(tuple,list)):
  for item in value:yield from _walk_keys(item)

def _valid_url(value):
 try:
  p=urlparse(value);return p.scheme=="https" and bool(p.netloc)
 except Exception:return False

def _event_ids():return {"event:"+e["id"] for e in policy_events.EVENTS}
def _index_ids():return {"index:"+r["id"] for r in systemic_registry.INDEXES}
def _company_ids():return {"company:"+r["id"] for r in systemic_registry.COMPANIES}
def _factor_ids(factors=FACTORS):return {"factor:"+r["id"] for r in factors}
def _theme_ids(themes=THEMES):return {"theme:"+r["id"] for r in themes}
def valid_refs(factors=FACTORS,themes=THEMES):return _event_ids()|_index_ids()|_company_ids()|_factor_ids(factors)|_theme_ids(themes)

def validate(relationships=RELATIONSHIPS,catalysts=CATALYSTS,factors=FACTORS,themes=THEMES):
 systemic_registry.validate();policy_events.validate_events(policy_events.EVENTS)
 if len(relationships)!=14 or len(catalysts)!=3:raise ValueError("phase1 relationship cardinality")
 if FORBIDDEN_KEYS.intersection(_walk_keys((relationships,catalysts))):raise ValueError("investment scoring data forbidden")
 refs=valid_refs(factors,themes)
 rel_ids=[]
 for rel in relationships:
  expected={"id","source_ref","target_ref","relation_type","claim_type","evidence_grade","claim","source_url","source_title","source_date","verified_at","invalidation","publication_state"}
  if set(rel)!=expected:raise ValueError("relationship shape")
  if rel["source_ref"] not in refs or rel["target_ref"] not in refs:raise ValueError("unknown relationship ref")
  if rel["source_ref"]==rel["target_ref"]:raise ValueError("self relationship")
  if rel["relation_type"] not in ALLOWED_RELATION_TYPES:raise ValueError("relationship type")
  if rel["claim_type"] not in ALLOWED_CLAIMS or rel["evidence_grade"] not in ALLOWED_GRADES:raise ValueError("claim discipline")
  if rel["claim_type"]=="FACT" and rel["evidence_grade"]!="A":raise ValueError("fact requires grade A")
  if rel["claim_type"]=="INFERENCE" and not rel["invalidation"].strip():raise ValueError("inference requires invalidation")
  if rel["publication_state"] not in ALLOWED_STATES:raise ValueError("publication state")
  if rel["evidence_grade"]=="C" and rel["publication_state"]!="confirm_required":raise ValueError("grade C must require confirmation")
  if rel["publication_state"]=="confirm_required" and rel["claim_type"]=="FACT":raise ValueError("unresolved fact cannot publish as fact")
  if not _valid_url(rel["source_url"]):raise ValueError("source url")
  if date.fromisoformat(rel["source_date"])>date.fromisoformat(rel["verified_at"]):raise ValueError("source date after verification")
  if rel["verified_at"]!=VERIFIED_AT:raise ValueError("verification date")
  if not rel["claim"].strip() or not rel["source_title"].strip() or not rel["invalidation"].strip():raise ValueError("empty relationship evidence")
  rel_ids.append(rel["id"])
 if len(rel_ids)!=len(set(rel_ids)):raise ValueError("duplicate relationship id")
 rel_id_set=set(rel_ids);catalyst_ids=[]
 for catalyst in catalysts:
  expected={"id","kind","trigger_event_ref","relationship_ids","monitor_window","activation_rule","invalidation","claim_type"}
  if set(catalyst)!=expected:raise ValueError("catalyst shape")
  if catalyst["kind"] not in {"scheduled_policy_event","structural_monitor"}:raise ValueError("catalyst kind")
  if catalyst["claim_type"]!="INFERENCE":raise ValueError("catalyst must remain inference")
  if catalyst["trigger_event_ref"] is not None and catalyst["trigger_event_ref"] not in _event_ids():raise ValueError("unknown catalyst event")
  if catalyst["kind"]=="scheduled_policy_event" and catalyst["trigger_event_ref"] is None:raise ValueError("scheduled catalyst event")
  if catalyst["kind"]=="structural_monitor" and catalyst["trigger_event_ref"] is not None:raise ValueError("structural catalyst event")
  ids=tuple(catalyst["relationship_ids"])
  if not ids or len(ids)!=len(set(ids)) or not set(ids)<=rel_id_set:raise ValueError("catalyst relationships")
  if not catalyst["monitor_window"].strip() or not catalyst["activation_rule"].strip() or not catalyst["invalidation"].strip():raise ValueError("catalyst text")
  catalyst_ids.append(catalyst["id"])
 if len(catalyst_ids)!=len(set(catalyst_ids)):raise ValueError("duplicate catalyst id")
 return {"schema_version":SCHEMA_VERSION,"verified_at":VERIFIED_AT,"relationship_count":len(relationships),"fact_count":sum(r["claim_type"]=="FACT" for r in relationships),"inference_count":sum(r["claim_type"]=="INFERENCE" for r in relationships),"confirm_required_count":sum(r["publication_state"]=="confirm_required" for r in relationships),"catalyst_count":len(catalysts),"publication_scope":PUBLICATION_SCOPE}

def by_id(relationship_id):
 matches=[r for r in RELATIONSHIPS if r["id"]==relationship_id]
 if len(matches)!=1:raise KeyError(relationship_id)
 return matches[0]

def _event_by_ref(event_ref,events):
 ident=event_ref.split(":",1)[1]
 matches=[e for e in events if e["id"]==ident]
 if len(matches)!=1:raise KeyError(event_ref)
 return matches[0]

def catalyst_state(catalyst,events=policy_events.EVENTS):
 if catalyst["kind"]=="structural_monitor":return "monitoring"
 event=_event_by_ref(catalyst["trigger_event_ref"],events)
 if event["outcome_state"]=="outcome_verified":return "outcome_verified_monitoring"
 if event["outcome_state"]=="cancelled_verified":return "cancelled_verified"
 return "pending_outcome_verification"

if __name__=="__main__":
 import json
 print(json.dumps(validate(),ensure_ascii=False,sort_keys=True))
