"""Scan the actual ticket application with Bandit and Semgrep."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--save-as', choices=['current','before','after'], default='current',
                    help='Preserve reports for the current code or a before/after comparison.')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
targets = ['tickets','chatbot','support_portal','mcp_server','guardrails','security']
out = root / 'results' / 'application' / args.save_as
out.mkdir(parents=True, exist_ok=True)
semgrep = str(Path(sys.executable).with_name('semgrep.exe' if os.name == 'nt' else 'semgrep'))
commands = [
    ('bandit',[sys.executable,'-m','bandit','-q','-r',*targets,'-f','json']),
    ('semgrep',[semgrep,'scan','--config',str(root/'scripts/semgrep.yml'),
        '--metrics=off','--disable-version-check','--no-git-ignore','--json',*targets]),
]
for name, command in commands:
    result = subprocess.run(command,cwd=root,capture_output=True,text=True,
        encoding='utf-8',errors='replace',env=dict(os.environ,SEMGREP_SEND_METRICS='off'))
    (out/(name+'.json')).write_text(result.stdout,encoding='utf-8')
    (out/(name+'.stderr.txt')).write_text(result.stderr,encoding='utf-8')
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f'{name} failed; see {out}')
    if result.returncode not in (0,1) or data.get('errors'):
        raise SystemExit(f'{name} scan failed; see {out}')
    print(f"{name}: {len(data.get('results',[]))} findings; {out/(name+'.json')}")
