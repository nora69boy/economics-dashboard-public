"""Normalize only the explicitly reviewed dashboard-presentation transform for rights hashing."""
from __future__ import annotations

import base64
import copy
import hashlib
import re

import publication_rights as rights

BADGE_OLD="badge('ARCHIVE SNAPSHOT / '+D.as_of,'p-warn')"
BADGE_NEW="badge('MARKET LIVE / PROVIDER-HOSTED','p-good')"
AGE_OLD="株価・指数: 2026-09-10固定 / マクロ: 各系列の観測日 / カレンダー: Source Healthを確認"
AGE_NEW="株価・指数: TradingView live（市場によりリアルタイム・遅延・EOD） / マクロ: 各系列の観測日 / カレンダー: Source Healthを確認"
LEGACY_OPEN='<div data-market-legacy="true" hidden aria-hidden="true">'
OLD_ARCHIVE='<div data-market-archive="true" class="notice"><strong>監査アーカイブ / 2026-09-10</strong><br>以下の自己ホスト株価・指数は権利レビュー前の固定スナップショットです。現在値・売買判断には使用せず、上段のライブWidgetを参照してください。</div>'
NEW_ARCHIVE='<div data-market-archive="true" class="notice"><strong>旧自己ホスト市場データは監査用に内部保持</strong><br>2026-09-10以前の固定値は通常表示から除外しました。現在の市場確認は上段のTradingView Widgetを使用してください。</div>'
WORLD_OLD='下段の2026-09-10固定値は監査用スナップショットです。'
MARKET_OLD='下段の2026-09-10以前の値は監査用スナップショットです。'
LIVE_NEW='旧固定値は監査用に内部保持し、通常画面では非表示です。'
OPERATIONS='<section class="panel" id="operations" aria-labelledby="tab-operations"><h2>出典・運用</h2>'

HEALTH_RE=re.compile(
 r'<section data-dashboard-health="true" class="p-card">'
 r'<div class="eyebrow">DASHBOARD HEALTH / CURRENT BUILD</div>'
 r'<h3>更新・取得・公開の状態</h3><div class="grid four">'
 r'<article class="card"><div class="eyebrow">MACRO</div><div class="metric (?:good|pending)">\d+/\d+ fresh</div><p class="small">最終取得試行 (?:\d{4}-\d{2}-\d{2} \d{2}:\d{2} JST|確認が必要)</p></article>'
 r'<article class="card"><div class="eyebrow">CALENDAR</div><div class="metric (?:good|pending)">(?:DEGRADED|PARTIAL ACCESS|FAMILY MERGE|REVIEWED STATIC)</div><p class="small">完全性ゲートを維持。取得障害時はレビュー済み日程を保持。</p></article>'
 r'<article class="card"><div class="eyebrow">MARKET</div><div class="metric good">LIVE VIEW</div><p class="small">TradingView provider-hosted。自己ホスト価格は権利ゲートで凍結し、通常表示から除外。</p></article>'
 r'<article class="card"><div class="eyebrow">BROWSER QA</div><div class="metric good">FAIL-CLOSED</div><p class="small">Chrome起動タイムアウトのみ最大1回再試行。その他の異常は公開停止。</p></article>'
 r'</div><p class="small">定期実行: JST 01:17 / 07:17 / 13:17 / 19:17 ・ Run (?:\d+|not-recorded) ・ 履歴成功率の蓄積表示は次段階。</p></section>'
)

def _require(ok):
    rights.require(ok,'UNMAPPED_HTML_CONTENT')

def _restore_panel(text,panel_id,next_id,old_live_note):
    marker=f'<section class="panel" id="{panel_id}"'
    next_marker=f'<section class="panel" id="{next_id}"'
    _require(text.count(marker)==1 and text.count(next_marker)==1)
    start=text.index(marker);end=text.index(next_marker,start);seg=text[start:end]
    _require(seg.count(LIVE_NEW)==1 and old_live_note not in seg)
    _require(seg.count(NEW_ARCHIVE)==1 and OLD_ARCHIVE not in seg)
    _require(seg.count(LEGACY_OPEN)==1)
    seg=seg.replace(LIVE_NEW,old_live_note,1).replace(NEW_ARCHIVE,OLD_ARCHIVE,1)
    open_at=seg.index(LEGACY_OPEN);outer=seg.rfind('</section>');close=seg.rfind('</div>',open_at,outer)
    _require(close>open_at and seg[close+len('</div>'):outer]=='')
    seg=seg[:open_at]+seg[open_at+len(LEGACY_OPEN):close]+seg[close+len('</div>'):]
    _require(LEGACY_OPEN not in seg and seg.count(OLD_ARCHIVE)==1)
    return text[:start]+seg+text[end:]

def _restore_csp(text):
    scripts=re.findall(r'<script\b([^>]*)>(.*?)</script\s*>',text,re.I|re.S)
    inline=[body for attrs,body in scripts if 'src=' not in attrs.lower()]
    _require(len(inline)==1)
    digest=base64.b64encode(hashlib.sha256(inline[0].encode()).digest()).decode()
    pattern=r"script-src 'sha256-[^']+'"
    _require(len(re.findall(pattern,text))==1)
    return re.sub(pattern,"script-src 'sha256-"+digest+"'",text,count=1)

def normalize_index(index_bytes):
    text=index_bytes.decode().replace('\r\n','\n')
    markers=(BADGE_NEW,AGE_NEW,'data-dashboard-health="true"',LEGACY_OPEN,NEW_ARCHIVE,LIVE_NEW)
    present=[m in text for m in markers]
    if not any(present):
        return index_bytes
    _require(all(present))
    _require(text.count(BADGE_NEW)==1 and text.count(BADGE_OLD)==0)
    _require(text.count(AGE_NEW)==1 and text.count(AGE_OLD)==0)
    _require(text.count(LEGACY_OPEN)==2 and text.count(NEW_ARCHIVE)==2 and text.count(LIVE_NEW)==2)
    _require(text.count(OPERATIONS)==1)
    op=text.index(OPERATIONS)+len(OPERATIONS)
    match=HEALTH_RE.match(text,op)
    _require(match is not None and text.count('data-dashboard-health="true"')==1)
    text=text[:op]+text[match.end():]
    text=_restore_panel(text,'world','market',WORLD_OLD)
    text=_restore_panel(text,'market','events',MARKET_OLD)
    text=text.replace(BADGE_NEW,BADGE_OLD,1).replace(AGE_NEW,AGE_OLD,1)
    _require(not any(m in text for m in markers))
    return _restore_csp(text).encode()

def normalize_payload(payload):
    out=copy.copy(payload)
    out['index.html']=normalize_index(payload['index.html'])
    return out
