#!/usr/bin/env python3
"""Validate reviewed public content before copying it to the Pages artifact.

This is a secondary deployment gate, not a guarantee of anonymity. A commit to
this public repository is public BEFORE this script runs. Review and scan in a
private staging area before pushing. Never import private history or records.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 1_000_000
EXTENSIONS = {'.html', '.json', '.md', '.css', '.js'}
PATTERNS = {
    'email': r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
    'phone': r'(?<!\d)(?:0\d{1,4}[- ]\d{1,4}[- ]\d{3,4}|0\d{9,10})(?!\d)',
    'international phone': r'(?<!\w)\+\d{1,3}[ -](?:\d[ -]?){7,14}(?!\d)',
    'credential': r'(?i)\b(?:api[_-]?key|access[_-]?token|secret|password|passwd)\b[\s\"\x27]*[:=][\s\"\x27]*[A-Za-z0-9_/-]{6,}',
    'token': r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b',
    'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'local address': r'(?i)(?:file://|localhost|\b127\.0\.0\.1\b|\b192\.168\.\d+\.\d+\b)',
}
TERMS = [
    '\u6c0f\u540d', '\u4f4f\u6240', '\u96fb\u8a71\u756a\u53f7', '\u751f\u5e74\u6708\u65e5',
    '\u30de\u30a4\u30ca\u30f3\u30d0\u30fc', '\u53e3\u5ea7\u756a\u53f7', '\u8a3c\u5238\u53e3\u5ea7',
    '\u4fdd\u6709\u682a\u6570', '\u53d6\u5f97\u5358\u4fa1', '\u8cb7\u4ed8\u4f59\u529b', '\u53e3\u5ea7\u6b8b\u9ad8',
    '\u8cc7\u7523\u7dcf\u984d', '\u542b\u307f\u76ca', '\u542b\u307f\u640d', '\u58f2\u8cb7\u5c65\u6b74',
    'home address', 'date of birth', 'account number', 'cost basis', 'account balance', 'trading history',
]
NETWORK = re.compile(r'(?i)\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\b|sendBeacon\b|EventSource\b|Worker\b|import\s*\(|eval\s*\(|Function\s*\(|location\b|localStorage\b|sessionStorage\b|indexedDB\b|cookie\b|FileReader\b|RTCPeerConnection\b)|window\s*\.\s*open')


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def normalized(text: str) -> str:
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m[1], 16)), text)
    return unicodedata.normalize('NFKC', html.unescape(text))


def scan(text: str) -> None:
    value = normalized(text)
    for label, pattern in PATTERNS.items():
        ensure(not re.search(pattern, value), 'sensitive pattern: ' + label)
    ensure(not any(t.lower() in value.lower() for t in TERMS), 'sensitive term')


class PageParser(HTMLParser):
    def __init__(self, allowed: set[str]):
        super().__init__(convert_charrefs=True)
        self.allowed = allowed
        self.csp = []
        self.referrer = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        ensure(tag not in {'iframe','object','embed','form','input','textarea','select','img','svg','math','audio','video','source','base','link'}, 'active tag: ' + tag)
        ensure(not any(k.lower().startswith('on') for k, _ in attrs), 'inline event handler')
        ensure(not any(k in values for k in ('src', 'srcset', 'srcdoc', 'ping')), 'resource attribute')
        if 'href' in values:
            href = values['href'] or ''
            ensure(href.startswith('#') or href in self.allowed, 'unapproved navigation')
        if tag == 'meta':
            kind = values.get('http-equiv', '').lower()
            ensure(kind != 'refresh', 'automatic navigation')
            if kind == 'content-security-policy':
                self.csp.append(values.get('content', ''))
            if values.get('name', '').lower() == 'referrer':
                self.referrer.append(values.get('content'))


def check_html(text: str, allowed: set[str]) -> None:
    page = PageParser(allowed)
    page.feed(text)
    scripts = re.findall(r'<script\b[^>]*>(.*?)</script\s*>', text, re.I | re.S)
    ensure(len(scripts) == 1, 'expected exactly one reviewed inline program')
    script = scripts[0]
    ensure(not NETWORK.search(normalized(script)), 'network or persistence program')
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    policy = ("default-src 'none'; script-src 'sha256-" + digest + "'; style-src 'unsafe-inline'; "
              "img-src 'none'; connect-src 'none'; font-src 'none'; object-src 'none'; frame-src 'none'; "
              "form-action 'none'; base-uri 'none'; upgrade-insecure-requests")
    ensure(page.csp == [policy], 'CSP missing, changed, or inline program hash mismatch')
    ensure(page.referrer == ['no-referrer'], 'no-referrer required')
    ensure(not re.search(r'@import|url\s*\(', text, re.I), 'CSS resource reference')
    ensure(text.rstrip().endswith('</html>'), 'incomplete HTML')


def validate_site(site: Path) -> dict[str, bytes]:
    ensure(site.is_dir() and not site.is_symlink(), 'site directory missing or linked')
    manifest_path = site / 'manifest.json'
    ensure(manifest_path.is_file() and not manifest_path.is_symlink(), 'manifest missing or linked')
    ensure(manifest_path.stat().st_size <= MAX_BYTES, 'oversized manifest')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    ensure(set(manifest) == {'version','classification','files'}, 'unexpected manifest fields')
    ensure(manifest['version'] == 2 and manifest['classification'] == 'public-market-research', 'manifest classification')
    files = manifest['files']
    ensure(isinstance(files, dict) and 'index.html' in files, 'empty or invalid allowlist')
    for name, digest in files.items():
        ensure(isinstance(name, str) and re.fullmatch(r'[a-z0-9][a-z0-9_./-]*', name) is not None, 'unsafe path')
        parts = PurePosixPath(name).parts
        ensure('..' not in parts and '.' not in parts and str(PurePosixPath(name)) == name, 'noncanonical path')
        ensure(Path(name).suffix in EXTENSIONS, 'unapproved extension')
        ensure(not any(p.startswith('.') or p in {'private','personal','accounts','credentials'} for p in parts), 'restricted path')
        ensure(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest) is not None, 'invalid digest')
    actual = set()
    for path in site.rglob('*'):
        ensure(not path.is_symlink(), 'symlink')
        ensure(path.is_file() or path.is_dir(), 'special file')
        if path.is_file():
            ensure(path.stat().st_nlink == 1, 'hardlink')
            actual.add(path.relative_to(site).as_posix())
    ensure(actual == set(files) | {'manifest.json'}, 'missing or unapproved site files')
    payload = {}
    for name, digest in sorted(files.items()):
        path = site / name
        ensure(path.stat().st_size <= MAX_BYTES, 'oversized payload')
        data = path.read_bytes()
        ensure(hashlib.sha256(data).hexdigest() == digest, 'unreviewed file hash')
        text = data.decode('utf-8')
        scan(text)
        if path.suffix == '.html':
            check_html(text, set(files))
        elif path.suffix == '.json':
            scan(json.dumps(json.loads(text), ensure_ascii=False))
        elif path.suffix in {'.js','.css'}:
            ensure(not NETWORK.search(normalized(text)), 'active code pattern')
        payload[name] = data
    return payload


def check_history() -> None:
    values = subprocess.check_output(['git','log','--all','--format=%ae%n%ce'], cwd=ROOT, text=True).splitlines()
    ensure(bool(values), 'no commit identity evidence')
    ensure(all(v == 'noreply@github.com' or v.endswith('@users.noreply.github.com') for v in values), 'non-noreply commit identity; value suppressed')
    allowed = {'README.md','.gitignore','scripts/check_site.py','tests/test_site.py','.github/workflows/pages.yml'}
    allowed |= {'site/' + p for p in validate_site(ROOT/'site')} | {'site/manifest.json'}
    tracked = set(subprocess.check_output(['git','ls-files'], cwd=ROOT, text=True).splitlines())
    ensure(tracked == allowed, 'unreviewed repository file set')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--check-history', action='store_true')
    args = parser.parse_args()
    payload = validate_site(ROOT/'site')
    if args.check_history:
        check_history()
    if args.build:
        dest = ROOT/'.pages-build'
        ensure(not dest.is_symlink(), 'linked artifact directory')
        if dest.exists():
            shutil.rmtree(dest)
        for name, data in payload.items():
            target = dest/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (dest/'.nojekyll').write_text('', encoding='utf-8')
    print(f'PASS: {len(payload)} reviewed payload files; sensitive values never printed')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError, subprocess.SubprocessError):
        raise SystemExit('PUBLICATION BLOCKED: validation failed; inspect privately, never paste sensitive values into logs')
