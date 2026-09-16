#!/usr/bin/env python3
"""Reviewed v0.7 systemic Entity / Index Registry Phase 1.

Identity metadata only: no market values, constituents, weights, fundamentals,
recommendations, portfolio state, or investment ranking. Company records are
issuer-level so ADR/local-line/share-class duplication cannot create duplicate
companies in downstream analysis.
"""
from __future__ import annotations

from urllib.parse import urlparse

SCHEMA_VERSION="0.7-registry1"
VERIFIED_AT="2026-09-16"
PUBLICATION_SCOPE="identity_metadata_only"
SELECTION_BASIS="architecture_seed_not_investment_ranking"

INDEXES=(
 {"id":"index-sp500","kind":"index","name":"S&P 500","provider":"S&P Dow Jones Indices","region":"US","reference_code":"SPX","source_url":"https://www.spglobal.com/spdji/en/indices/equity/sp-500/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-nasdaq100","kind":"index","name":"Nasdaq-100 Index","provider":"Nasdaq","region":"US","reference_code":"NDX","source_url":"https://www.nasdaq.com/products/global-indexes/nasdaq-100","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-nasdaq-composite","kind":"index","name":"NASDAQ Composite","provider":"Nasdaq","region":"US","reference_code":"COMP","source_url":"https://indexes.nasdaq.com/Index/Overview/COMP","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-sox","kind":"index","name":"PHLX Semiconductor Sector Index","provider":"Nasdaq","region":"US","reference_code":"SOX","source_url":"https://indexes.nasdaq.com/Index/Overview/SOX","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-russell2000","kind":"index","name":"Russell 2000 Index","provider":"FTSE Russell / LSEG","region":"US","reference_code":None,"source_url":"https://www.lseg.com/en/ftse-russell/indices/russell-2000-index","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-nikkei225","kind":"index","name":"Nikkei Stock Average (Nikkei 225)","provider":"Nikkei Inc.","region":"JP","reference_code":None,"source_url":"https://indexes.nikkei.co.jp/en/nkave/index/profile","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-topix","kind":"index","name":"TOPIX","provider":"JPX Market Innovation & Research","region":"JP","reference_code":"TPX","source_url":"https://www.jpx.co.jp/english/markets/indices/topix/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-tse-growth250","kind":"index","name":"Tokyo Stock Exchange Growth Market 250 Index","provider":"JPX Market Innovation & Research","region":"JP","reference_code":None,"source_url":"https://www.jpx.co.jp/english/markets/indices/factsheets/files/e_200_fac2_growth%20250.pdf","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-taiex","kind":"index","name":"TWSE Capitalization Weighted Stock Index (TAIEX)","provider":"Taiwan Stock Exchange","region":"TW","reference_code":"TAIEX","source_url":"https://twse-regulation.twse.com.tw/EN/law/DOC01_print.aspx?FLCODE=FL047579&FLNO=1","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-kospi","kind":"index","name":"KOSPI","provider":"Korea Exchange","region":"KR","reference_code":"KOSPI","source_url":"https://global.krx.co.kr/main/main.jsp","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-hstech","kind":"index","name":"Hang Seng TECH Index","provider":"Hang Seng Indexes","region":"HK","reference_code":"HSTECH","source_url":"https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hsteche.pdf","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"index-stoxx600","kind":"index","name":"STOXX Europe 600","provider":"STOXX","region":"EU","reference_code":"SXXP","source_url":"https://stoxx.com/index/sxxp/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
)

COMPANIES=(
 {"id":"company-nvidia","kind":"company","name":"NVIDIA Corporation","jurisdiction":"US","canonical_instrument":{"venue":"NASDAQ","symbol":"NVDA","instrument_type":"common"},"alternate_instruments":(),"dedupe_group":"issuer:nvidia","source_url":"https://investor.nvidia.com/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-microsoft","kind":"company","name":"Microsoft Corporation","jurisdiction":"US","canonical_instrument":{"venue":"NASDAQ","symbol":"MSFT","instrument_type":"common"},"alternate_instruments":(),"dedupe_group":"issuer:microsoft","source_url":"https://www.microsoft.com/en-us/investor/faq","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-alphabet","kind":"company","name":"Alphabet Inc.","jurisdiction":"US","canonical_instrument":{"venue":"NASDAQ","symbol":"GOOGL","instrument_type":"class_a_common"},"alternate_instruments":({"venue":"NASDAQ","symbol":"GOOG","instrument_type":"class_c_capital"},),"dedupe_group":"issuer:alphabet","source_url":"https://abc.xyz/investor/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-amazon","kind":"company","name":"Amazon.com, Inc.","jurisdiction":"US","canonical_instrument":{"venue":"NASDAQ","symbol":"AMZN","instrument_type":"common"},"alternate_instruments":(),"dedupe_group":"issuer:amazon","source_url":"https://ir.aboutamazon.com/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-broadcom","kind":"company","name":"Broadcom Inc.","jurisdiction":"US","canonical_instrument":{"venue":"NASDAQ","symbol":"AVGO","instrument_type":"common"},"alternate_instruments":(),"dedupe_group":"issuer:broadcom","source_url":"https://investors.broadcom.com/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-tsmc","kind":"company","name":"Taiwan Semiconductor Manufacturing Company Limited","jurisdiction":"TW","canonical_instrument":{"venue":"TWSE","symbol":"2330","instrument_type":"common"},"alternate_instruments":({"venue":"NYSE","symbol":"TSM","instrument_type":"adr"},),"dedupe_group":"issuer:tsmc","source_url":"https://investor.tsmc.com/english/shareholder-services/stock-quotes","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-skhynix","kind":"company","name":"SK hynix Inc.","jurisdiction":"KR","canonical_instrument":{"venue":"KRX","symbol":"000660","instrument_type":"common"},"alternate_instruments":(),"dedupe_group":"issuer:skhynix","source_url":"https://www.skhynix.com/ir/UI-FR-IR03/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-advantest","kind":"company","name":"Advantest Corporation","jurisdiction":"JP","canonical_instrument":{"venue":"TSE_PRIME","symbol":"6857","instrument_type":"common"},"alternate_instruments":({"venue":"US_OTC_ADR","symbol":"ATEYY","instrument_type":"adr"},),"dedupe_group":"issuer:advantest","source_url":"https://www.advantest.com/en/investors/shares-and-corporate-bonds/share-information/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-tokyo-electron","kind":"company","name":"Tokyo Electron Limited","jurisdiction":"JP","canonical_instrument":{"venue":"TSE_PRIME","symbol":"8035","instrument_type":"common"},"alternate_instruments":(),"dedupe_group":"issuer:tokyo-electron","source_url":"https://www.tel.com/ir/stocks/info/","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-mufg","kind":"company","name":"Mitsubishi UFJ Financial Group, Inc.","jurisdiction":"JP","canonical_instrument":{"venue":"TSE_PRIME","symbol":"8306","instrument_type":"common"},"alternate_instruments":(),"dedupe_group":"issuer:mufg","source_url":"https://www.mufg.jp/english/ir/index.html","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-ntt","kind":"company","name":"NTT, Inc.","jurisdiction":"JP","canonical_instrument":{"venue":"TSE_PRIME","symbol":"9432","instrument_type":"common"},"alternate_instruments":(),"dedupe_group":"issuer:ntt","source_url":"https://group.ntt/en/ir/shares/digest.html","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
 {"id":"company-rocket-lab","kind":"company","name":"Rocket Lab Corporation","jurisdiction":"US","canonical_instrument":{"venue":"NASDAQ","symbol":"RKLB","instrument_type":"common"},"alternate_instruments":(),"dedupe_group":"issuer:rocket-lab","source_url":"https://investors.rocketlabcorp.com/resources/investor-faqs","verified_at":VERIFIED_AT,"evidence_grade":"A","publication_scope":PUBLICATION_SCOPE},
)

FORBIDDEN_KEYS={"price","index_level","market_cap","weight","revenue","earnings","valuation","score","recommendation","position_size","probability"}

def _walk_keys(value):
 if isinstance(value,dict):
  for key,item in value.items():
   yield key
   yield from _walk_keys(item)
 elif isinstance(value,(tuple,list)):
  for item in value:yield from _walk_keys(item)

def _valid_url(value):
 try:
  parsed=urlparse(value)
  return parsed.scheme=="https" and bool(parsed.netloc)
 except Exception:return False

def instrument_key(instrument):
 return instrument["venue"]+":"+instrument["symbol"]

def validate(indexes=INDEXES,companies=COMPANIES):
 if len(indexes)!=12 or len(companies)!=12:raise ValueError("phase1 registry cardinality")
 all_records=tuple(indexes)+tuple(companies)
 ids=[r["id"] for r in all_records]
 if len(ids)!=len(set(ids)):raise ValueError("duplicate registry id")
 if FORBIDDEN_KEYS.intersection(_walk_keys(all_records)):raise ValueError("non-identity data in registry")
 for record in all_records:
  if record["publication_scope"]!=PUBLICATION_SCOPE:raise ValueError("publication scope")
  if record["evidence_grade"]!="A" or record["verified_at"]!=VERIFIED_AT:raise ValueError("verification metadata")
  if not _valid_url(record["source_url"]):raise ValueError("source url")
 for record in indexes:
  if record["kind"]!="index" or not record["name"] or not record["provider"] or not record["region"]:raise ValueError("index record")
 owners={};groups=set()
 for record in companies:
  if record["kind"]!="company" or not record["name"] or not record["jurisdiction"]:raise ValueError("company record")
  if not record["dedupe_group"].startswith("issuer:") or record["dedupe_group"] in groups:raise ValueError("issuer dedupe group")
  groups.add(record["dedupe_group"])
  instruments=(record["canonical_instrument"],)+tuple(record["alternate_instruments"])
  if len({instrument_key(i) for i in instruments})!=len(instruments):raise ValueError("duplicate instrument within issuer")
  for instrument in instruments:
   if set(instrument)!={"venue","symbol","instrument_type"}:raise ValueError("instrument shape")
   key=instrument_key(instrument)
   if key in owners and owners[key]!=record["id"]:raise ValueError("instrument assigned to multiple issuers")
   owners[key]=record["id"]
 return {"schema_version":SCHEMA_VERSION,"verified_at":VERIFIED_AT,"index_count":len(indexes),"company_count":len(companies),"instrument_count":len(owners),"publication_scope":PUBLICATION_SCOPE,"selection_basis":SELECTION_BASIS}

def by_id(record_id):
 matches=[r for r in tuple(INDEXES)+tuple(COMPANIES) if r["id"]==record_id]
 if len(matches)!=1:raise KeyError(record_id)
 return matches[0]

def issuer_for_instrument(venue,symbol):
 key=venue+":"+symbol
 for company in COMPANIES:
  for instrument in (company["canonical_instrument"],)+tuple(company["alternate_instruments"]):
   if instrument_key(instrument)==key:return company["id"]
 return None

if __name__=="__main__":
 import json
 print(json.dumps(validate(),ensure_ascii=False,sort_keys=True))
