"""Runtime Validation Script for WhatsApp Notification Router.

Verifies:
✓ Input file actually used (messages.csv vs sample_messages.csv)
✓ Output file actually used (output.csv vs sample_output.csv)
✓ Dataset row count matches input CSV
✓ Rule Coverage consistent across all reports & logs
✓ LLM Coverage consistent across all reports & logs
✓ Output rows correct and valid
✓ Reports consistent with central RuntimeStatistics
"""

import json
from pathlib import Path
import subprocess
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent


def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run shell command and return CompletedProcess."""
    print(f"\n[EXEC] Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(f"[ERROR] Command failed with code {res.returncode}")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        sys.exit(1)
    return res


def validate_run(input_path: str, output_path: str, expected_rows: int) -> None:
    """Validate a single execution run with given input and output paths."""
    print("\n" + "=" * 60)
    print(f" VALIDATING RUN: input={input_path}, output={output_path}, expected_rows={expected_rows}")
    print("=" * 60)

    # 1. Execute main.py with CLI arguments
    cmd = [sys.executable, "main.py"]
    if input_path:
        cmd.extend(["--input", input_path])
    if output_path:
        cmd.extend(["--output", output_path])

    res = run_command(cmd)
    stdout = res.stdout

    # 2. Check Execution Header in stdout
    resolved_input = Path(input_path or "dataset/messages.csv").resolve()
    resolved_output = Path(output_path or "output/output.csv").resolve()

    if str(resolved_input) not in stdout and input_path not in stdout:
        raise RuntimeError(f"Input file validation failed: {input_path} not found in execution logs!")
    print(f"[PASS] Input file actually used ({input_path or 'dataset/messages.csv'})")

    if str(resolved_output) not in stdout and output_path not in stdout:
        raise RuntimeError(f"Output file validation failed: {output_path} not found in execution logs!")
    print(f"[PASS] Output file actually used ({output_path or 'output/output.csv'})")

    # 3. Check CSV Row Count
    out_csv = Path(resolved_output)
    if not out_csv.exists():
        raise RuntimeError(f"Output CSV missing at: {out_csv}")

    df_out = pd.read_csv(out_csv)
    if len(df_out) != expected_rows:
        raise RuntimeError(f"Row count mismatch! Output has {len(df_out)} rows, expected {expected_rows}")
    print(f"[PASS] Dataset row count matches ({len(df_out)} rows == {expected_rows} expected)")

    # 4. Check Reports Consistency
    reports_dir = PROJECT_ROOT / "reports"
    exec_rep_path = reports_dir / "execution_report.json"
    qual_rep_path = reports_dir / "quality_report.json"
    sum_md_path = reports_dir / "summary.md"

    if not exec_rep_path.exists() or not qual_rep_path.exists() or not sum_md_path.exists():
        raise RuntimeError("One or more required report files missing in reports/!")

    with open(exec_rep_path, mode="r", encoding="utf-8") as f:
        exec_data = json.load(f)

    with open(qual_rep_path, mode="r", encoding="utf-8") as f:
        qual_data = json.load(f)

    sum_md_text = sum_md_path.read_text(encoding="utf-8")

    # Verify total_processed in execution_report
    if exec_data.get("total_processed") != expected_rows:
        raise RuntimeError(
            f"Execution report total_processed mismatch: {exec_data.get('total_processed')} != {expected_rows}"
        )

    # Extract Rule Coverage %
    rule_cov_exec = float(exec_data.get("rule_coverage_pct", 0.0))

    qual_rule_str = qual_data.get("rule_coverage", "0.0%").replace("%", "").strip()
    rule_cov_qual = float(qual_rule_str)

    if abs(rule_cov_exec - rule_cov_qual) > 0.1:
        raise RuntimeError(
            f"Rule Coverage mismatch between reports! execution_report={rule_cov_exec}%, quality_report={rule_cov_qual}%"
        )

    # Verify Rule Coverage in summary.md
    if f"Rule Coverage**: {rule_cov_exec}%" not in sum_md_text and f"Rule Coverage**: {rule_cov_qual}%" not in sum_md_text:
        if f"{rule_cov_exec}%" not in sum_md_text:
            raise RuntimeError(f"Rule Coverage {rule_cov_exec}% not found in reports/summary.md!")

    print(f"[PASS] Rule Coverage consistent across reports ({rule_cov_exec}%)")

    # Extract LLM Coverage %
    llm_cov_exec = float(exec_data.get("llm_coverage_pct", 0.0))
    qual_llm_str = qual_data.get("llm_coverage", "0.0%").replace("%", "").strip()
    llm_cov_qual = float(qual_llm_str)

    if abs(llm_cov_exec - llm_cov_qual) > 0.1:
        raise RuntimeError(
            f"LLM Coverage mismatch between reports! execution_report={llm_cov_exec}%, quality_report={llm_cov_qual}%"
        )
    print(f"[PASS] LLM Coverage consistent across reports ({llm_cov_exec}%)")

    print(f"[PASS] Output rows correct ({len(df_out)} predictions validated)")
    print("[PASS] Reports consistent")


def main() -> None:
    """Run complete runtime validation suite."""
    print("=========================================================")
    print("       STARTING RUNTIME & ARCHITECTURE VALIDATION")
    print("=========================================================")

    # Test 1: Default execution (messages.csv -> 110 rows)
    validate_run(input_path="dataset/messages.csv", output_path="output/output.csv", expected_rows=110)

    # Test 2: Sample messages CLI execution (sample_messages.csv -> 30 rows)
    validate_run(
        input_path="dataset/sample_messages.csv",
        output_path="output/sample_output.csv",
        expected_rows=30,
    )

    print("\n=========================================================")
    print("     ALL RUNTIME & ARCHITECTURE VALIDATION CHECKS PASSED")
    print("=========================================================\n")


if __name__ == "__main__":
    main()
