#!/usr/bin/env python3
"""PostToolUse(Agent) hook: security gate for scan certification.

Receives both tool_input (exact prompt sent) and tool_response
(subagent output) in one payload. Verifies:
1. The prompt was exactly "scan this repo" (conformance)
2. The scan completed with zero findings (pass=true)
3. HEAD SHA hasn't changed since pre-scan-capture.py ran

Writes cert only when all checks pass.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

CACHE_DIR = os.path.expanduser("~/.cache/claude-coding-plugin")
EXPECTED_PROMPT = "scan this repo"


def get_head_sha():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return None


def extract_scan_result(response_text):
    """Extract privacy-guard-result JSON from the response."""
    match = re.search(
        r"```privacy-guard-result\s*\n(.*?)\n```",
        response_text, re.DOTALL,
    )
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Fallback: look for any JSON with status field
    for m in re.finditer(r"\{[^{}]*\"status\"[^{}]*\}", response_text, re.DOTALL):
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Only care about Agent tool completions
    if data.get("tool_name") != "Agent":
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")

    if "privacy" not in subagent_type.lower():
        sys.exit(0)

    # --- Check 1: Prompt conformance ---
    prompt = tool_input.get("prompt", "").strip().lower()
    if prompt != EXPECTED_PROMPT:
        # Non-conformant prompt — do not certify
        sys.exit(0)

    # --- Check 2: Scan result ---
    tool_response = data.get("tool_response", "")
    if isinstance(tool_response, dict):
        # May be structured — extract text content
        content = tool_response.get("content", "")
        if isinstance(content, list):
            text_parts = [
                p.get("text", "") for p in content
                if isinstance(p, dict) and p.get("type") == "text"
            ]
            tool_response = "\n".join(text_parts)
        elif isinstance(content, str):
            tool_response = content
        else:
            tool_response = json.dumps(tool_response)

    scan_result = extract_scan_result(str(tool_response))
    if not scan_result:
        # No parseable scan result — do not certify
        sys.exit(0)

    status = scan_result.get("status")
    findings = scan_result.get("findings", [])

    if status != "completed" or len(findings) > 0:
        # Scan did not pass — do not certify
        sys.exit(0)

    # --- Check 3: HEAD SHA unchanged ---
    current_sha = get_head_sha()
    if not current_sha:
        sys.exit(0)

    pre_scan_file = os.path.join(CACHE_DIR, "pre-scan-sha")
    if os.path.isfile(pre_scan_file):
        with open(pre_scan_file) as f:
            pre_scan_sha = f.read().strip()
        if pre_scan_sha != current_sha:
            # Repo mutated during scan — do not certify
            sys.exit(0)

    # --- All checks passed: write cert ---
    os.makedirs(CACHE_DIR, exist_ok=True)
    cert_path = os.path.join(CACHE_DIR, f"scan-{current_sha}.cert")
    with open(cert_path, "w") as f:
        f.write("true")

    # Clean up pre-scan sha
    if os.path.isfile(pre_scan_file):
        os.unlink(pre_scan_file)

    sys.exit(0)


if __name__ == "__main__":
    main()
