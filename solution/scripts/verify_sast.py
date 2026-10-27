"""Verify scanner findings in the real ticket application."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--secured',action='store_true',help='Require completed application repairs.')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
secured = args.secured or root.name == 'solution'
subprocess.run([sys.executable,str(root/'scripts/run_sast.py')],check=True)
reports = root/'results/application/current'
semgrep = json.loads((reports/'semgrep.json').read_text())
ids = {row['check_id'].split('.')[-1] for row in semgrep['results']}
expected = set() if secured else {'workshop-model-selected-dispatch'}
if ids != expected:
    raise SystemExit('Unexpected application scanner findings: '+', '.join(sorted(ids)) + '. Use --secured after completing repairs.')
bandit = json.loads((reports/'bandit.json').read_text())
if any(row['issue_severity']=='HIGH' for row in bandit['results']):
    raise SystemExit('Review HIGH Bandit findings in results/application/current/bandit.json.')
if not secured:
    print('Application scan checks passed. Authorization repairs are verified by request tests.')
else:
    print('Application checks passed.')
