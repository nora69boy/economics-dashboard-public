"""Run all 88 legacy regressions in an isolated original four-file fixture."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 dst=Path(tmp)
 for folder in ['templates','scripts','tests','site/data','site/reports']:(dst/folder).mkdir(parents=True,exist_ok=True)
 names=['scripts/build_dashboard.py','scripts/check_site.py','scripts/source_policy.json','tests/test_site.py','templates/base.html','templates/charts.js','templates/charts.css','site/data/current-state.json','site/data/market.json','site/reports/2026-09-11-carry-forward.md']
 for n in names:shutil.copy2(ROOT/n,dst/n)
 subprocess.run([sys.executable,'scripts/build_dashboard.py'],cwd=dst,check=True)
 files=['index.html','data/current-state.json','data/market.json','reports/2026-09-11-carry-forward.md'];hashes={f:hashlib.sha256((dst/'site'/f).read_bytes()).hexdigest() for f in files}
 if hashes['index.html']!='48c804f57b189675ab779f30a817ee2f1835502b049129664aefa38bf5043370':raise SystemExit('Legacy fixture changed: review required')
 (dst/'site/manifest.json').write_text(json.dumps({'version':2,'classification':'public-market-research','files':hashes}))
 subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_site.py','-v'],cwd=dst,check=True)
