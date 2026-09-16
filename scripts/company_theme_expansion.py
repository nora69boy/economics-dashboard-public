#!/usr/bin/env python3
"""v0.7 Company / Theme Relationship Expansion Phase 1.

Adds evidence-backed coverage for the seven seed issuers that were not yet
connected to a company/theme relationship in the base registry. This module is
backend/source-of-truth only in Phase 1: it does not add prices, rankings,
probabilities, recommendations, or portfolio actions to the public dashboard.
"""
from __future__ import annotations

import json
from datetime import date
from urllib.parse import urlparse

import relationship_registry
import systemic_registry

SCHEMA_VERSION = "0.7-company-theme1"
VERIFIED_AT = "2026-09-17"
PUBLICATION_SCOPE = "evidence_backed_company_theme_relationships"
ALLOWED_RELATION_TYPES = {"business_exposure", "demand_exposure", "earnings_sensitivity", "technology_strategy"}
ALLOWED_HOSTS = {
    "www.microsoft.com",
    "www.sec.gov",
    "investors.broadcom.com",
    "www.mufg.jp",
    "group.ntt",
    "investors.rocketlabcorp.com",
}

THEMES = (
    {"id": "theme-ai-cloud-infrastructure", "kind": "theme", "name": "AI cloud / datacenter infrastructure"},
    {"id": "theme-ai-networking-accelerators", "kind": "theme", "name": "Custom AI accelerators / AI networking"},
    {"id": "theme-photonics-ai-infrastructure", "kind": "theme", "name": "Photonics-enabled AI infrastructure"},
    {"id": "theme-space-launch-systems", "kind": "theme", "name": "Launch services / space systems demand"},
)

RELATIONSHIPS = (
    {
        "id": "rel-ai-cloud-microsoft",
        "source_ref": "theme:theme-ai-cloud-infrastructure",
        "target_ref": "company:company-microsoft",
        "relation_type": "business_exposure",
        "claim_type": "FACT",
        "evidence_grade": "A",
        "claim": "Microsoft reports expanding datacenter and GPU capacity in response to accelerating cloud and AI demand, while customer demand continues to exceed available Azure capacity.",
        "source_url": "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4",
        "source_title": "Microsoft Fiscal Year 2026 Fourth Quarter Earnings Conference Call",
        "source_published_at": "2026-07-29",
        "verified_at": VERIFIED_AT,
        "invalidation": "A later Microsoft filing or earnings call no longer identifies AI/cloud demand or capacity expansion as a material infrastructure driver.",
        "publication_state": "publishable",
    },
    {
        "id": "rel-ai-cloud-alphabet",
        "source_ref": "theme:theme-ai-cloud-infrastructure",
        "target_ref": "company:company-alphabet",
        "relation_type": "business_exposure",
        "claim_type": "FACT",
        "evidence_grade": "A",
        "claim": "Alphabet reports Google Cloud growth driven in part by enterprise AI solutions and AI infrastructure and is allocating capital to scale AI infrastructure and global compute.",
        "source_url": "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000066/googexhibit991q22026.htm",
        "source_title": "Alphabet Second Quarter 2026 Results - Exhibit 99.1",
        "source_published_at": "2026-07-22",
        "verified_at": VERIFIED_AT,
        "invalidation": "A later Alphabet filing materially weakens the disclosed link between Google Cloud growth, AI infrastructure demand, and infrastructure investment.",
        "publication_state": "publishable",
    },
    {
        "id": "rel-ai-cloud-amazon",
        "source_ref": "theme:theme-ai-cloud-infrastructure",
        "target_ref": "company:company-amazon",
        "relation_type": "business_exposure",
        "claim_type": "FACT",
        "evidence_grade": "A",
        "claim": "Amazon reports rapid AWS AI and chip-business growth and states that the increase in capital investment primarily reflects investments in artificial intelligence.",
        "source_url": "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000024/amzn-20260630xex991.htm",
        "source_title": "Amazon.com Second Quarter 2026 Results - Exhibit 99.1",
        "source_published_at": "2026-07-30",
        "verified_at": VERIFIED_AT,
        "invalidation": "A later Amazon filing materially weakens the disclosed link between AWS growth, AI demand, and infrastructure investment.",
        "publication_state": "publishable",
    },
    {
        "id": "rel-ai-networking-broadcom",
        "source_ref": "theme:theme-ai-networking-accelerators",
        "target_ref": "company:company-broadcom",
        "relation_type": "demand_exposure",
        "claim_type": "FACT",
        "evidence_grade": "A",
        "claim": "Broadcom reports very strong demand for custom AI accelerators and networking and identifies AI semiconductor demand as a major current growth driver.",
        "source_url": "https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2026-financial",
        "source_title": "Broadcom Third Quarter Fiscal Year 2026 Financial Results",
        "source_published_at": "2026-09-02",
        "verified_at": VERIFIED_AT,
        "invalidation": "A later Broadcom results release materially weakens the custom-accelerator or AI-networking demand linkage.",
        "publication_state": "publishable",
    },
    {
        "id": "rel-jp-rates-mufg",
        "source_ref": "factor:factor-jp-policy-rate",
        "target_ref": "company:company-mufg",
        "relation_type": "earnings_sensitivity",
        "claim_type": "FACT",
        "evidence_grade": "A",
        "claim": "MUFG reports that rising yen interest rates increased loan and deposit interest income and contributed to higher net operating profit; its FY2026 plan also includes a BOJ policy-rate assumption.",
        "source_url": "https://www.mufg.jp/dam/ir/presentation/2025/pdf/speech2603_en.pdf",
        "source_title": "MUFG FY2025 IR Presentation Speech Script",
        "source_published_at": "2026-05-19",
        "verified_at": VERIFIED_AT,
        "invalidation": "A later MUFG filing shows that yen-rate changes no longer have a material positive relationship with loan/deposit interest income or materially changes the disclosed rate assumptions.",
        "publication_state": "publishable",
    },
    {
        "id": "rel-photonics-ntt",
        "source_ref": "theme:theme-photonics-ai-infrastructure",
        "target_ref": "company:company-ntt",
        "relation_type": "technology_strategy",
        "claim_type": "FACT",
        "evidence_grade": "A",
        "claim": "NTT identifies AIOWN as AI-native next-generation infrastructure that optimizes GPU, network, and power resources and is expanding All-Photonics Network and photonics-electronics convergence commercialization.",
        "source_url": "https://group.ntt/en/corporate/press_conference/2026/05/260508.html",
        "source_title": "NTT Financial Results for the Fourth Quarter of FY2025 ended March 31, 2026 - CEO Press Conference",
        "source_published_at": "2026-05-08",
        "verified_at": VERIFIED_AT,
        "invalidation": "A later NTT strategy update materially abandons AIOWN, APN expansion, or photonics-electronics convergence as a core AI-infrastructure initiative.",
        "publication_state": "publishable",
    },
    {
        "id": "rel-space-systems-rocket-lab",
        "source_ref": "theme:theme-space-launch-systems",
        "target_ref": "company:company-rocket-lab",
        "relation_type": "business_exposure",
        "claim_type": "FACT",
        "evidence_grade": "A",
        "claim": "Rocket Lab reports demand across launch services and space systems and describes both businesses as core contributors to its current contract backlog and growth activity.",
        "source_url": "https://investors.rocketlabcorp.com/news-releases/news-release-details/rocket-lab-announces-second-quarter-2026-financial-results-posts",
        "source_title": "Rocket Lab Second Quarter 2026 Financial Results",
        "source_published_at": "2026-08-10",
        "verified_at": VERIFIED_AT,
        "invalidation": "A later Rocket Lab filing materially changes the launch/space-systems business mix or no longer supports demand across those two operating areas.",
        "publication_state": "publishable",
    },
)

MONITORS = (
    {
        "id": "monitor-hyperscaler-ai-capacity-2026h2",
        "relationship_ids": ("rel-ai-cloud-microsoft", "rel-ai-cloud-alphabet", "rel-ai-cloud-amazon"),
        "monitor_window": "through the next quarterly earnings cycle",
        "activation_rule": "Keep the theme active only while primary disclosures continue to show AI/cloud demand alongside infrastructure or capacity expansion.",
        "invalidation": "Two or more of the three issuers materially reduce AI/cloud capacity plans or disclose demand deterioration inconsistent with the current theme.",
        "claim_type": "INFERENCE",
    },
    {
        "id": "monitor-ai-networking-broadcom-2026h2",
        "relationship_ids": ("rel-ai-networking-broadcom",),
        "monitor_window": "through Broadcom's next earnings cycle",
        "activation_rule": "Maintain only while company primary disclosures continue to describe strong custom AI accelerator and networking demand.",
        "invalidation": "Broadcom materially cuts the disclosed AI semiconductor/networking demand outlook or identifies a structural demand reversal.",
        "claim_type": "INFERENCE",
    },
    {
        "id": "monitor-jp-rate-mufg-fy26",
        "relationship_ids": ("rel-jp-rates-mufg",),
        "monitor_window": "through MUFG FY2026 results",
        "activation_rule": "Track only as earnings sensitivity; a BOJ rate move alone is not a directional stock signal.",
        "invalidation": "MUFG disclosures show rate effects are offset or reversed by funding costs, hedging, credit costs, or other factors such that the current earnings-sensitivity interpretation no longer holds.",
        "claim_type": "INFERENCE",
    },
    {
        "id": "monitor-photonics-ai-infra-2026-27",
        "relationship_ids": ("rel-photonics-ntt",),
        "monitor_window": "through FY2027 APN and photonics commercialization milestones",
        "activation_rule": "Track official NTT deployment and commercialization milestones rather than treating technology announcements as realized earnings.",
        "invalidation": "NTT materially delays or abandons APN/photonics commercialization milestones or no longer positions AIOWN as core AI infrastructure.",
        "claim_type": "INFERENCE",
    },
    {
        "id": "monitor-space-launch-systems-2026",
        "relationship_ids": ("rel-space-systems-rocket-lab",),
        "monitor_window": "through Rocket Lab's next quarterly filing",
        "activation_rule": "Track signed contracts, backlog conversion, launch execution, and space-systems delivery using company filings; do not infer share-price direction from backlog alone.",
        "invalidation": "Material contract cancellations, execution delays, or a later filing that reverses the disclosed demand picture across launch and space systems.",
        "claim_type": "INFERENCE",
    },
)

FORBIDDEN_KEYS = {"price", "target_price", "probability", "buy_score", "score", "recommendation", "position_size", "ranking"}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_keys(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from _walk_keys(item)


def _valid_url(value):
    try:
        parsed = urlparse(value)
        return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS
    except Exception:
        return False


def _theme_refs(themes=THEMES):
    return {"theme:" + item["id"] for item in themes}


def _valid_refs(themes=THEMES):
    return relationship_registry.valid_refs() | _theme_refs(themes)


def _company_refs(records):
    refs = set()
    for record in records:
        for field in ("source_ref", "target_ref"):
            ref = record[field]
            if ref.startswith("company:"):
                refs.add(ref.split(":", 1)[1])
    return refs


def covered_company_ids():
    return _company_refs(relationship_registry.RELATIONSHIPS) | _company_refs(RELATIONSHIPS)


def missing_company_ids():
    expected = {company["id"] for company in systemic_registry.COMPANIES}
    return tuple(sorted(expected - covered_company_ids()))


def validate(relationships=RELATIONSHIPS, monitors=MONITORS, themes=THEMES):
    systemic_registry.validate()
    relationship_registry.validate()
    if len(relationships) != 7 or len(monitors) != 5 or len(themes) != 4:
        raise ValueError("phase1 expansion cardinality")
    if FORBIDDEN_KEYS.intersection(_walk_keys((relationships, monitors))):
        raise ValueError("investment scoring data forbidden")
    theme_ids = [item["id"] for item in themes]
    if len(theme_ids) != len(set(theme_ids)):
        raise ValueError("duplicate theme id")
    refs = _valid_refs(themes)
    rel_ids = []
    target_companies = []
    expected_shape = {"id", "source_ref", "target_ref", "relation_type", "claim_type", "evidence_grade", "claim", "source_url", "source_title", "source_published_at", "verified_at", "invalidation", "publication_state"}
    for rel in relationships:
        if set(rel) != expected_shape:
            raise ValueError("relationship shape")
        if rel["source_ref"] not in refs or rel["target_ref"] not in refs:
            raise ValueError("unknown relationship ref")
        if rel["relation_type"] not in ALLOWED_RELATION_TYPES:
            raise ValueError("relationship type")
        if rel["claim_type"] != "FACT" or rel["evidence_grade"] != "A":
            raise ValueError("expansion facts require grade A")
        if rel["publication_state"] != "publishable":
            raise ValueError("phase1 facts must be publishable")
        if rel["verified_at"] != VERIFIED_AT or not _valid_url(rel["source_url"]):
            raise ValueError("verification metadata")
        if date.fromisoformat(rel["source_published_at"]) > date.fromisoformat(rel["verified_at"]):
            raise ValueError("source date after verification")
        if not rel["claim"].strip() or not rel["source_title"].strip() or not rel["invalidation"].strip():
            raise ValueError("empty evidence field")
        if not rel["target_ref"].startswith("company:"):
            raise ValueError("phase1 target must be company")
        rel_ids.append(rel["id"])
        target_companies.append(rel["target_ref"].split(":", 1)[1])
    if len(rel_ids) != len(set(rel_ids)):
        raise ValueError("duplicate relationship id")
    if len(target_companies) != len(set(target_companies)):
        raise ValueError("one expansion relationship per uncovered issuer")
    base_covered = _company_refs(relationship_registry.RELATIONSHIPS)
    if base_covered.intersection(target_companies):
        raise ValueError("phase1 expansion duplicates already-covered issuer")
    if missing_company_ids():
        raise ValueError("seed issuer coverage incomplete")
    monitor_ids = []
    rel_id_set = set(rel_ids)
    monitor_shape = {"id", "relationship_ids", "monitor_window", "activation_rule", "invalidation", "claim_type"}
    for monitor in monitors:
        if set(monitor) != monitor_shape or monitor["claim_type"] != "INFERENCE":
            raise ValueError("monitor shape")
        ids = tuple(monitor["relationship_ids"])
        if not ids or len(ids) != len(set(ids)) or not set(ids) <= rel_id_set:
            raise ValueError("monitor relationship refs")
        if not monitor["monitor_window"].strip() or not monitor["activation_rule"].strip() or not monitor["invalidation"].strip():
            raise ValueError("monitor text")
        monitor_ids.append(monitor["id"])
    if len(monitor_ids) != len(set(monitor_ids)):
        raise ValueError("duplicate monitor id")
    return {
        "schema_version": SCHEMA_VERSION,
        "verified_at": VERIFIED_AT,
        "theme_count": len(themes),
        "relationship_count": len(relationships),
        "monitor_count": len(monitors),
        "seed_company_coverage": len(covered_company_ids()),
        "publication_scope": PUBLICATION_SCOPE,
    }


def canonical_dump():
    payload = {"themes": THEMES, "relationships": RELATIONSHIPS, "monitors": MONITORS, "metadata": validate()}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    print(canonical_dump())
