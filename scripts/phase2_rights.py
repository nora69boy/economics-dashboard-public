"""Fail-closed normalizer for reviewed v0.7 Phase 2 presentation only."""
from __future__ import annotations
import copy
import phase2_overview
import presentation_rights
import publication_rights as rights


def _require(value):rights.require(value,'UNMAPPED_HTML_CONTENT')


def normalize_index(index_bytes):
 text=index_bytes.decode().replace('\r\n','\n')
 marker=phase2_overview.MARKER
 runtime=[new in text for _,new in phase2_overview.RUNTIME_PAIRS]
 if marker not in text and not any(runtime):return presentation_rights.normalize_index(index_bytes)
 _require(text.count(marker)==1 and all(runtime))
 block=phase2_overview.relevance_block();_require(text.count(block)==1)
 text=text.replace(block,'',1)
 _require(text.count(phase2_overview.PHASE5)==1 and phase2_overview.PHASE4 not in text)
 text=text.replace(phase2_overview.PHASE5,phase2_overview.PHASE4,1)
 for old,new in phase2_overview.RUNTIME_PAIRS:
  _require(text.count(new)==1 and text.count(old)==0);text=text.replace(new,old,1)
 text=phase2_overview._restore_csp(text)
 _require(marker not in text and not any(new in text for _,new in phase2_overview.RUNTIME_PAIRS))
 return presentation_rights.normalize_index(text.encode())


def normalize_payload(payload):
 out=copy.copy(payload);out['index.html']=normalize_index(payload['index.html']);return out
