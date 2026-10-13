#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="aquasec/trivy:0.75.0"
REPORT="$ROOT/trivy-report.json"
TEMP_REPORT="$ROOT/.trivy-report.tmp.json"

cleanup() {
  rm -f "$TEMP_REPORT"
}
trap cleanup EXIT

echo "==> Scanning: $ROOT"
echo "==> Scanner: $IMAGE"

docker run --rm \
  -v "$ROOT:/work" \
  -w /work \
  "$IMAGE" \
  fs \
  --scanners vuln,misconfig,secret \
  --skip-files .env \
  --skip-dirs node_modules \
  --format json \
  --output /work/.trivy-report.tmp.json \
  /work

python3 - "$TEMP_REPORT" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    report = json.load(f)

results = report.get("Results") or []
vulns = [
    v
    for result in results
    for v in (result.get("Vulnerabilities") or [])
]
misconfigs = [
    item
    for result in results
    for item in (result.get("Misconfigurations") or [])
]
secrets = [
    item
    for result in results
    for item in (result.get("Secrets") or [])
]

print("\n==> Scan summary")
print(f"Vulnerabilities: {len(vulns)}")
print(f"Misconfigurations: {len(misconfigs)}")
print(f"Secrets: {len(secrets)}")

severity_counts = {}
for vuln in vulns:
    severity = vuln.get("Severity", "UNKNOWN").upper()
    severity_counts[severity] = severity_counts.get(severity, 0) + 1

for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"):
    if severity_counts.get(severity):
        print(f"  {severity}: {severity_counts[severity]}")
PY

mv "$TEMP_REPORT" "$REPORT"

echo
echo "==> Scan complete"
echo "==> Report saved to: $REPORT"
