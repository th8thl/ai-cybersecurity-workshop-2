from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Finding:
    title: str
    severity: str
    file: str
    evidence: str
    recommendation: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def scan() -> list[Finding]:
    findings: list[Finding] = []
    views = PROJECT_ROOT / "chatbot" / "views.py"

    if views.exists():
        text = read_text(views)
        if "defended_response_for" not in text:
            findings.append(
                Finding(
                    title="Input guardrail is not wired into the request path",
                    severity="High",
                    file=str(views.relative_to(PROJECT_ROOT)),
                    evidence="defended_response_for not imported or called",
                    recommendation="Call defended_response_for before sending user input to the model.",
                )
            )

    gitignore = PROJECT_ROOT / ".gitignore"
    if not gitignore.exists() or ".env" not in read_text(gitignore):
        findings.append(
            Finding(
                title=".env is not ignored",
                severity="High",
                file=".gitignore",
                evidence="Missing .env entry",
                recommendation="Add .env to .gitignore before creating local API keys.",
            )
        )

    return findings


def main() -> None:
    findings = scan()
    if not findings:
        print("No high-risk findings.")
        return

    for index, finding in enumerate(findings, start=1):
        print(f"{index}. [{finding.severity}] {finding.title}")
        print(f"   File: {finding.file}")
        print(f"   Evidence: {finding.evidence}")
        print(f"   Recommendation: {finding.recommendation}")
        print()


if __name__ == "__main__":
    main()
