#!/usr/bin/env python3
"""Typed strategic policy-event model for the v0.7 migration.

The model separates an official schedule from an observed/verified outcome.
Crossing a scheduled timestamp never promotes an event to completed.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

CLAIM_CLASSES={"FACT","ESTIMATE","INFERENCE","RUMOR"}
TIME_PRECISION={"exact","date_only","unknown"}
OUTCOME_STATES={"scheduled","outcome_verified","cancelled_verified"}

FED_SOURCE="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
BOJ_MEETING_SOURCE="https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm"
BOJ_RELEASE_SOURCE="https://www.boj.or.jp/about/calendar/index.htm"

EVENTS=(
 {
  "id":"fomc-statement-2026-09","group_id":"policy-2026-09-fed-boj","authority":"Federal Reserve",
  "event_type":"policy_statement","scheduled_date":"2026-09-17","scheduled_at":"2026-09-17T03:00:00+09:00",
  "time_precision":"exact","outcome_state":"scheduled","outcome_verified_at":None,
  "valid_from":"2026-09-15T00:00:00+09:00","valid_until":"2026-09-20T23:59:59+09:00",
  "source_url":FED_SOURCE,"claim_class":"FACT",
 },
 {
  "id":"fomc-press-conference-2026-09","group_id":"policy-2026-09-fed-boj","authority":"Federal Reserve",
  "event_type":"press_conference","scheduled_date":"2026-09-17","scheduled_at":"2026-09-17T03:30:00+09:00",
  "time_precision":"exact","outcome_state":"scheduled","outcome_verified_at":None,
  "valid_from":"2026-09-15T00:00:00+09:00","valid_until":"2026-09-20T23:59:59+09:00",
  "source_url":FED_SOURCE,"claim_class":"FACT",
 },
 {
  "id":"boj-policy-decision-2026-09","group_id":"policy-2026-09-fed-boj","authority":"Bank of Japan",
  "event_type":"policy_decision","scheduled_date":"2026-09-18","scheduled_at":None,
  "time_precision":"unknown","outcome_state":"scheduled","outcome_verified_at":None,
  "valid_from":"2026-09-15T00:00:00+09:00","valid_until":"2026-09-20T23:59:59+09:00",
  "source_url":BOJ_RELEASE_SOURCE,"claim_class":"FACT",
 },
 {
  "id":"boj-governor-press-conference-2026-09","group_id":"policy-2026-09-fed-boj","authority":"Bank of Japan",
  "event_type":"press_conference","scheduled_date":"2026-09-18","scheduled_at":"2026-09-18T15:30:00+09:00",
  "time_precision":"exact","outcome_state":"scheduled","outcome_verified_at":None,
  "valid_from":"2026-09-15T00:00:00+09:00","valid_until":"2026-09-20T23:59:59+09:00",
  "source_url":BOJ_MEETING_SOURCE,"claim_class":"FACT",
 },
)

class PolicyEventError(ValueError):
 pass

def _require(ok:bool,message:str)->None:
 if not ok:raise PolicyEventError(message)

def _aware(value:str,label:str)->datetime:
 _require(isinstance(value,str) and value,f"{label} must be a timestamp")
 try:parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
 except ValueError as exc:raise PolicyEventError(f"{label} must be ISO-8601") from exc
 _require(parsed.tzinfo is not None and parsed.utcoffset() is not None,f"{label} must include timezone")
 return parsed

def validate_event(event:dict[str,Any])->dict[str,Any]:
 expected={"id","group_id","authority","event_type","scheduled_date","scheduled_at","time_precision","outcome_state","outcome_verified_at","valid_from","valid_until","source_url","claim_class"}
 _require(isinstance(event,dict) and set(event)==expected,"event fields mismatch")
 for key in ("id","group_id","authority","event_type","scheduled_date","source_url"):_require(isinstance(event[key],str) and event[key],f"{key} required")
 _require(event["time_precision"] in TIME_PRECISION,"invalid time_precision")
 _require(event["outcome_state"] in OUTCOME_STATES,"invalid outcome_state")
 _require(event["claim_class"] in CLAIM_CLASSES,"invalid claim_class")
 start=_aware(event["valid_from"],"valid_from");end=_aware(event["valid_until"],"valid_until");_require(start<end,"valid window must increase")
 if event["time_precision"]=="exact":_aware(event["scheduled_at"],"scheduled_at")
 else:_require(event["scheduled_at"] is None,"non-exact schedule cannot invent a timestamp")
 if event["outcome_state"]=="scheduled":_require(event["outcome_verified_at"] is None,"scheduled outcome cannot have verification time")
 else:_aware(event["outcome_verified_at"],"outcome_verified_at")
 return event

def validate_events(events=EVENTS):
 ids=[]
 for event in events:validate_event(event);ids.append(event["id"])
 _require(len(ids)==len(set(ids)),"event ids must be unique")
 return events

def by_id(event_id:str,events=EVENTS):
 validate_events(events)
 for event in events:
  if event["id"]==event_id:return event
 raise PolicyEventError("unknown event id")

def active_event_ids(at:datetime,events=EVENTS):
 _require(at.tzinfo is not None and at.utcoffset() is not None,"at must be timezone-aware")
 validate_events(events);out=[]
 for event in events:
  if _aware(event["valid_from"],"valid_from")<=at<=_aware(event["valid_until"],"valid_until"):out.append(event["id"])
 return out

def phase_at(at:datetime,events=EVENTS):
 """Return a conservative phase; schedule passage alone never means completion."""
 _require(at.tzinfo is not None and at.utcoffset() is not None,"at must be timezone-aware")
 validate_events(events)
 ordered=[by_id("fomc-statement-2026-09",events),by_id("fomc-press-conference-2026-09",events),by_id("boj-governor-press-conference-2026-09",events)]
 first=ordered[0];first_at=_aware(first["scheduled_at"],"scheduled_at")
 if at<first_at:return "pre_fomc"
 if first["outcome_state"]!="outcome_verified":return "fomc_statement_due_unverified"
 second=ordered[1];second_at=_aware(second["scheduled_at"],"scheduled_at")
 if at<second_at:return "fomc_statement_verified_press_conference_pending"
 if second["outcome_state"]!="outcome_verified":return "fomc_press_conference_due_unverified"
 boj=by_id("boj-policy-decision-2026-09",events)
 if boj["outcome_state"]!="outcome_verified":return "boj_decision_pending_or_due_unverified"
 boj_pc=ordered[2];boj_pc_at=_aware(boj_pc["scheduled_at"],"scheduled_at")
 if at<boj_pc_at:return "boj_decision_verified_press_conference_pending"
 if boj_pc["outcome_state"]!="outcome_verified":return "boj_press_conference_due_unverified"
 return "post_policy_events_verified"

def runtime_time_line(events=EVENTS):
 """Return the exact reviewed schedule line expected in the legacy runtime shell."""
 statement=by_id("fomc-statement-2026-09",events)
 press=by_id("fomc-press-conference-2026-09",events)
 boj_press=by_id("boj-governor-press-conference-2026-09",events)
 return "const fomc=Date.parse('%s'),fomcPc=Date.parse('%s'),bojPc=Date.parse('%s');"%(statement["scheduled_at"],press["scheduled_at"],boj_press["scheduled_at"])

def runtime_render_js(events=EVENTS):
 """Generate browser phase logic from verified outcome flags, not clock passage alone."""
 validate_events(events)
 verified=lambda event_id: str(by_id(event_id,events)["outcome_state"]=="outcome_verified").lower()
 flags=("const fomcVerified=%s,fomcPcVerified=%s,bojVerified=%s,bojPcVerified=%s;"%(
  verified("fomc-statement-2026-09"),verified("fomc-press-conference-2026-09"),
  verified("boj-policy-decision-2026-09"),verified("boj-governor-press-conference-2026-09")))
 render=("function render(){const n=Date.now();let p='事前レンジ',a='イベント前の金利・為替・株式の方向を確認';"
  "if(n<fomc){stage.textContent='FOMC声明待ち';countdown.textContent='FOMC声明まで '+left(fomc,n);}" 
  "else if(!fomcVerified){stage.textContent='FOMC声明予定時刻経過 / 結果確認待ち';countdown.textContent='公式結果を確認するまで通過扱いにしません';p='FOMC結果未確認';a='FRB公式発表を確認してから市場反応を判定';}"
  "else if(n<fomcPc){stage.textContent='FOMC声明確認済み / 議長会見待ち';countdown.textContent='議長会見まで '+left(fomcPc,n);p='FOMC声明確認済み';a='会見後の米10年金利とNASDAQの方向一致を確認';}"
  "else if(!fomcPcVerified){stage.textContent='FOMC会見予定時刻経過 / 結果確認待ち';countdown.textContent='会見内容を確認するまでFOMC通過扱いにしません';p='FOMC会見結果未確認';a='FRB公式会見情報を確認してから次フェーズへ進む';}"
  "else if(!bojVerified){stage.textContent='FOMC確認済み / 日銀決定確認待ち';countdown.textContent='日銀政策決定内容の公表時刻は未定。公式公表を確認';p='FOMC確認済み / BOJ未確認';a='日銀の決定内容を時刻推測せず確認';}"
  "else if(n<bojPc){stage.textContent='日銀決定確認済み / 総裁会見待ち';countdown.textContent='日銀総裁会見まで '+left(bojPc,n);p='BOJ決定確認済み';a='会見後のUSD/JPYと日本株の方向一致を確認';}"
  "else if(!bojPcVerified){stage.textContent='日銀会見予定時刻経過 / 結果確認待ち';countdown.textContent='公式会見内容を確認するまで政策イベント通過扱いにしません';p='BOJ会見結果未確認';a='日銀公式情報を確認してから24時間反応を評価';}"
  "else{stage.textContent='FOMC・日銀結果確認済み / 市場反応を検証';countdown.textContent='金利・USD/JPY・TOPIX・日経225の24時間反応を確認';p='24時間フォロースルー';a='イベント前レンジへ戻るか、方向性が定着するかを確認';}"
  "if(phase)phase.textContent=p;if(action)action.textContent=a;}")
 return flags+"\n"+render

validate_events()
