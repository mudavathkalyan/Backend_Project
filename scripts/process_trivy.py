#!/usr/bin/env python3

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from stix2 import Bundle, Identity, Vulnerability

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "trivy-report.json"
OUTPUT_DIR = ROOT / "security-output"

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")


def main():
    if not INPUT_FILE.is_file():
        raise SystemExit(f"Trivy report not found: {INPUT_FILE}")

    with INPUT_FILE.open(encoding="utf-8") as f:
        report = json.load(f)

    results = report.get("Results") or []
    occurrences = []
    by_cve = {}

    for result in results:
        target = result.get("Target", "Unknown target")

        for finding in result.get("Vulnerabilities") or []:
            cve = finding.get("VulnerabilityID")
            if not cve:
                continue

            occurrence = {
                "cve": cve,
                "target": target,
                "package": finding.get("PkgName", "Unknown package"),
                "installed_version": finding.get("InstalledVersion", "Unknown"),
                "fixed_version": finding.get("FixedVersion") or None,
                "severity": (finding.get("Severity") or "UNKNOWN").upper(),
                "title": finding.get("Title") or "",
                "description": finding.get("Description") or "",
                "primary_url": finding.get("PrimaryURL") or None,
            }
            occurrences.append(occurrence)
            by_cve.setdefault(cve, []).append(occurrence)

    severity_counts = Counter(
        item["severity"] for item in occurrences
    )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_report": INPUT_FILE.name,
        "total_vulnerability_occurrences": len(occurrences),
        "unique_cves": len(by_cve),
        "severity_counts": {
            severity: severity_counts.get(severity, 0)
            for severity in SEVERITIES
        },
        "misconfigurations": sum(
            len(r.get("Misconfigurations") or []) for r in results
        ),
        "secrets": sum(
            len(r.get("Secrets") or []) for r in results
        ),
        "findings": occurrences,
    }

    identity = Identity(
        name="Trivy Vulnerability Scanner",
        identity_class="tool",
    )

    objects = [identity]

    for cve, findings in sorted(by_cve.items()):
        details = []
        for item in findings:
            details.append(
                f"Target: {item['target']}; "
                f"Package: {item['package']}; "
                f"Installed: {item['installed_version']}; "
                f"Fixed: {item['fixed_version'] or 'Not specified'}; "
                f"Severity: {item['severity']}"
            )

        description = "\n".join(details)
        original_description = next(
            (item["description"] for item in findings if item["description"]),
            "",
        )
        if original_description:
            description += "\n\nVulnerability description:\n" + original_description

        # Prefer a valid CVE/NVD reference when the finding is a CVE.
        references = []
        if cve.startswith("CVE-"):
            references.append({
                "source_name": "NVD",
                "external_id": cve,
                "url": f"https://nvd.nist.gov/vuln/detail/{cve}",
            })

        primary_url = next(
            (item["primary_url"] for item in findings if item["primary_url"]),
            None,
        )
        if primary_url and not any(
            ref.get("url") == primary_url for ref in references
        ):
            references.append({
                "source_name": "Trivy",
                "url": primary_url,
            })

        vuln = Vulnerability(
            name=cve,
            description=description,
            external_references=references or None,
            created_by_ref=identity.id,
        )
        objects.append(vuln)

    bundle = Bundle(objects=objects)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = OUTPUT_DIR / "summary.json"
    stix_path = OUTPUT_DIR / "trivy-stix-2.1.json"

    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    stix_path.write_text(
        bundle.serialize(pretty=True),
        encoding="utf-8",
    )

    print("Trivy report processed successfully")
    print(f"Vulnerability occurrences: {len(occurrences)}")
    print(f"Unique CVEs: {len(by_cve)}")
    print(f"STIX objects: {len(objects)}")
    print(f"Severity counts: {dict(severity_counts)}")
    print(f"Summary: {summary_path}")
    print(f"STIX bundle: {stix_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
