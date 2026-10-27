"""One command runs the documented readiness/security checks without changing student data."""
import argparse
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--secured',action='store_true',help='Require full security checks for a repaired starter')
parser.add_argument('--semantic',action='store_true',help='Also use local Qwen for semantic NeMo and agent checks')
args=parser.parse_args()
secured=args.secured or root.name=='solution'
labels=["tests"] if secured else ['tests.test_ai_client', 'tests.test_prompt_security', 'tests.test_ticket_portal', 'tests.test_chat_storage', 'tests.test_verified_outcomes', 'tests.test_planner', 'tests.test_web_security', 'tests.test_context_security', 'tests.test_authorization']
commands=[
    [sys.executable,'manage.py','test',*labels],
    [sys.executable,'scripts/healthcheck.py',*(['--secured'] if secured else []),*(['--semantic'] if args.semantic else [])],
    [sys.executable,'scripts/verify_sast.py',*(['--secured'] if secured else [])],
]
for command in commands:
    subprocess.run(command,cwd=root,check=True)
if secured:
    subprocess.run([sys.executable,'guardrails/compare.py','--configured'],cwd=root,check=True)
print('All requested workshop checks passed.')
