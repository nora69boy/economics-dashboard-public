#!/usr/bin/env python3
"""v0.7 Relevance Scoring Phase 1.

Research-attention prioritization across all reviewed relationships. This is not
an investment score: no price target, probability, recommendation, expected
return, ranking, or position sizing is produced. The three axes are independent:
Market Impact, Catalyst Urgency, and Evidence Strength (0-5).
"""
from __future__ import annotations

import json

import company_theme_expansion as expansion
import relationship_registry as relationships

SCHEMA_VERSION = "0.7-relevance1"
REVIEWED_AT = "2026-09-17T00:53:00+09:00"
PUBLICATION_SCOPE = "research_attention_prioritization_not_investment_ranking"
AXES = ("market_impact", "catalyst_urgency", "evidence_strength")
ATTENTION_STATES = {5: "immediate", 4: "active", 3: "watch", 2: "structural", 1: "structural", 0: "structural"}
EVIDENCE_STRENGTH = {"A": 5, "B": 4, "C": 2}
FORBIDDEN_KEYS = {"price", "target_price", "probability", "buy_score", "recommendation", "position_size", "ranking", "expected_return", "priority_total"}


def _r(relationship_id, market_impact, catalyst_urgency, driver_ref, rationale, urgency_basis):
    return {
        "relationship_id": relationship_id,
        "market_impact": market_impact,
        "catalyst_urgency": catalyst_urgency,
        "evidence_strength": 0,
        "attention_state": ATTENTION_STATES[catalyst_urgency],
        "driver_ref": driver_ref,
        "rationale": rationale,
        "urgency_basis": urgency_basis,
        "reviewed_at": REVIEWED_AT,
    }


RECORDS = (
    _r("rel-fomc-policy-rate", 5, 5, "catalyst:catalyst-fomc-2026-09", "FOMC policy stance is a system-level rate input with broad cross-asset transmission.", "Scheduled FOMC outcome is pending verification; immediate source verification is required before interpretation."),
    _r("rel-us-rate-financial-conditions", 5, 5, "catalyst:catalyst-fomc-2026-09", "U.S. financial conditions transmit policy changes into rates, asset prices and funding conditions.", "Directly linked to the pending FOMC catalyst window."),
    _r("rel-us-financial-sp500", 5, 5, "catalyst:catalyst-fomc-2026-09", "S&P 500 is a broad U.S. equity observation point for policy transmission.", "Event-window market response is immediately relevant around the scheduled FOMC decision."),
    _r("rel-us-financial-nasdaq100", 5, 5, "catalyst:catalyst-fomc-2026-09", "Nasdaq-100 is a high-duration growth-equity observation point for policy transmission.", "Event-window market response is immediately relevant around the scheduled FOMC decision."),
    _r("rel-fomc-usd-channel", 5, 5, "catalyst:catalyst-fomc-2026-09", "The U.S. dollar is a major global transmission channel for relative rates and financial conditions.", "Directly linked to the pending FOMC catalyst window."),
    _r("rel-boj-policy-rate", 5, 5, "catalyst:catalyst-boj-2026-09", "BOJ policy is a system-level input for yen rates, FX and Japanese assets.", "September BOJ meeting is active and the policy statement timing is not pre-assumed."),
    _r("rel-boj-usdjpy", 5, 5, "catalyst:catalyst-boj-2026-09", "USD/JPY is a core observation channel for Japan/U.S. rate-differential transmission.", "Directly linked to the active BOJ catalyst window."),
    _r("rel-usdjpy-topix", 4, 5, "catalyst:catalyst-boj-2026-09", "TOPIX provides broad Japan-equity confirmation or rejection of an FX-led interpretation.", "Directly linked to the active BOJ catalyst window."),
    _r("rel-ai-demand-tsmc", 5, 4, "catalyst:catalyst-ai-semi-demand-2026q3", "TSMC is a central manufacturing node for leading-edge AI/HPC demand transmission.", "Structural AI semiconductor chain remains active through the next issuer earnings cycle."),
    _r("rel-ai-demand-skhynix", 5, 4, "catalyst:catalyst-ai-semi-demand-2026q3", "SK hynix is a central HBM/memory node in current AI infrastructure demand.", "Structural AI semiconductor chain remains active through the next issuer earnings cycle."),
    _r("rel-ai-demand-advantest", 4, 4, "catalyst:catalyst-ai-semi-demand-2026q3", "Tester demand is a useful downstream signal for AI semiconductor volume and complexity.", "Structural AI semiconductor chain remains active through the next issuer earnings cycle."),
    _r("rel-ai-demand-tel", 4, 4, "catalyst:catalyst-ai-semi-demand-2026q3", "WFE demand provides a capital-equipment transmission point for AI data-center semiconductor investment.", "Structural AI semiconductor chain remains active through the next issuer earnings cycle."),
    _r("rel-nvidia-tsmc", 5, 4, "catalyst:catalyst-ai-semi-demand-2026q3", "The disclosed NVIDIA-TSMC manufacturing dependency links accelerator demand to leading-edge foundry capacity.", "Supplier relationship remains material to the active AI semiconductor monitoring cycle."),
    _r("rel-nvidia-skhynix", 5, 4, "catalyst:catalyst-ai-semi-demand-2026q3", "The disclosed NVIDIA-SK hynix memory sourcing relationship links accelerator demand to HBM supply.", "Supplier relationship remains material to the active AI semiconductor monitoring cycle."),
    _r("rel-ai-cloud-microsoft", 5, 4, "monitor:monitor-hyperscaler-ai-capacity-2026h2", "Microsoft AI/cloud capacity is a major demand signal for data-center compute infrastructure.", "Monitor remains active through the next quarterly earnings cycle."),
    _r("rel-ai-cloud-alphabet", 5, 4, "monitor:monitor-hyperscaler-ai-capacity-2026h2", "Alphabet AI/cloud infrastructure spending is a major hyperscaler demand signal.", "Monitor remains active through the next quarterly earnings cycle."),
    _r("rel-ai-cloud-amazon", 5, 4, "monitor:monitor-hyperscaler-ai-capacity-2026h2", "AWS AI infrastructure and chip investment are major hyperscaler demand signals.", "Monitor remains active through the next quarterly earnings cycle."),
    _r("rel-ai-networking-broadcom", 5, 4, "monitor:monitor-ai-networking-broadcom-2026h2", "Broadcom custom accelerators and AI networking are direct infrastructure demand observation points.", "Monitor remains active through Broadcom's next earnings cycle."),
    _r("rel-jp-rates-mufg", 4, 4, "monitor:monitor-jp-rate-mufg-fy26", "MUFG provides a direct earnings-sensitivity observation point for changes in yen rates.", "BOJ meeting proximity raises research urgency, but this remains an earnings-sensitivity monitor rather than a directional stock signal."),
    _r("rel-photonics-ntt", 3, 2, "monitor:monitor-photonics-ai-infra-2026-27", "NTT AIOWN/photonics may matter structurally for future AI infrastructure efficiency, but commercialization is longer-dated.", "Monitor horizon is through FY2027 commercialization milestones."),
    _r("rel-space-systems-rocket-lab", 3, 3, "monitor:monitor-space-launch-systems-2026", "Rocket Lab launch and space-systems execution can materially affect company-specific operating outcomes, with lower broad-market transmission.", "Track signed contracts, backlog conversion and execution through the next quarterly filing."),
)


def _all_relationships():
    return relationships.RELATIONSHIPS + expansion.RELATIONSHIPS


def _relationship_map():
    return {r["id"]: r for r in _all_relationships()}


def _driver_map():
    result = {}
    for item in relationships.CATALYSTS:
        result["catalyst:" + item["id"]] = ("catalyst", item)
    for item in expansion.MONITORS:
        result["monitor:" + item["id"]] = ("monitor", item)
    return result


def hydrated_records(records=RECORDS):
    rels = _relationship_map()
    out = []
    for record in records:
        value = dict(record)
        rel = rels[value["relationship_id"]]
        value["evidence_strength"] = EVIDENCE_STRENGTH[rel["evidence_grade"]]
        out.append(value)
    return tuple(out)


def validate(records=RECORDS):
    relationships.validate();expansion.validate()
    rels = _relationship_map();drivers = _driver_map();values = hydrated_records(records)
    if len(values) != 21 or len(rels) != 21:
        raise ValueError("phase1 relevance cardinality")
    if set(r["relationship_id"] for r in values) != set(rels):
        raise ValueError("relevance relationship coverage")
    if len({r["relationship_id"] for r in values}) != len(values):
        raise ValueError("duplicate relevance relationship")
    expected = {"relationship_id", "market_impact", "catalyst_urgency", "evidence_strength", "attention_state", "driver_ref", "rationale", "urgency_basis", "reviewed_at"}
    for record in values:
        if set(record) != expected:
            raise ValueError("relevance record shape")
        for axis in AXES:
            if type(record[axis]) is not int or not 0 <= record[axis] <= 5:
                raise ValueError("relevance axis range")
        rel = rels[record["relationship_id"]]
        if record["evidence_strength"] != EVIDENCE_STRENGTH[rel["evidence_grade"]]:
            raise ValueError("evidence strength mismatch")
        if record["attention_state"] != ATTENTION_STATES[record["catalyst_urgency"]]:
            raise ValueError("attention state mismatch")
        if record["driver_ref"] not in drivers:
            raise ValueError("unknown relevance driver")
        driver_kind, driver = drivers[record["driver_ref"]]
        if record["relationship_id"] not in set(driver["relationship_ids"]):
            raise ValueError("driver does not cover relationship")
        if driver_kind == "catalyst":
            state = relationships.catalyst_state(driver)
            if state in {"pending_outcome_verification", "outcome_verified_monitoring"} and record["catalyst_urgency"] != 5:
                raise ValueError("active policy catalyst requires urgency 5")
            if state == "cancelled_verified" and record["catalyst_urgency"] != 0:
                raise ValueError("cancelled policy catalyst requires urgency 0")
        else:
            if record["catalyst_urgency"] > 4:
                raise ValueError("structural monitor urgency cap")
        if not record["rationale"].strip() or not record["urgency_basis"].strip():
            raise ValueError("relevance rationale")
        if record["reviewed_at"] != REVIEWED_AT:
            raise ValueError("relevance review timestamp")
    if FORBIDDEN_KEYS.intersection({k for r in values for k in r}):
        raise ValueError("investment decision field forbidden")
    counts = {name: sum(r["attention_state"] == name for r in values) for name in {"immediate", "active", "watch", "structural"}}
    return {
        "schema_version": SCHEMA_VERSION,
        "reviewed_at": REVIEWED_AT,
        "relationship_count": len(values),
        "immediate_count": counts["immediate"],
        "active_count": counts["active"],
        "watch_count": counts["watch"],
        "structural_count": counts["structural"],
        "publication_scope": PUBLICATION_SCOPE,
    }


def by_relationship_id(relationship_id):
    matches = [r for r in hydrated_records() if r["relationship_id"] == relationship_id]
    if len(matches) != 1:
        raise KeyError(relationship_id)
    return matches[0]


def canonical_dump():
    return json.dumps({"metadata": validate(), "records": hydrated_records()}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    print(canonical_dump())
