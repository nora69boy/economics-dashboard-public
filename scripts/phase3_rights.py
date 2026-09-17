"""Fail-closed normalizer for reviewed v0.7 Market Feed Health presentation."""
from __future__ import annotations
import copy,json
import phase2_rights
import phase3_feed_health as phase3
import publication_rights as rights


def _require(value):rights.require(value,'UNMAPPED_HTML_CONTENT')


def normalize_payload(payload):
 out=copy.copy(payload);text=payload['index.html'].decode().replace('\r\n','\n')
 if phase3.MARKER not in text:return phase2_rights.normalize_payload(payload)
 _require(text.count(phase3.MARKER)==1 and text.count(phase3.PHASE6)==1 and phase3.PHASE5 not in text)
 macro=json.loads(payload['data/macro.json'])
 block=phase3.feed_health_block(macro);_require(text.count(block)==1)
 text=text.replace(block,'',1).replace(phase3.PHASE6,phase3.PHASE5,1)
 _require(phase3.MARKER not in text)
 out['index.html']=text.encode()
 return phase2_rights.normalize_payload(out)
