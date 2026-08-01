"""
verify_output.py — Independent output.csv checker for the Notification Router.

Run this yourself, separately from whatever coding agent generated output.csv.
It does not trust any self-reported summary — it recomputes every metric directly
from the CSVs, the same way Claude did by hand in this conversation.

Usage:
    python verify_output.py --dataset dataset --output output/output.csv

Exits non-zero if any check fails, so you can also drop this into a CI step or
just run it before every submission.
"""

import argparse
import sys
import pandas as pd


def load(dataset_dir, output_path):
    messages = pd.read_csv(f"{dataset_dir}/messages.csv")
    history = pd.read_csv(f"{dataset_dir}/message_history.csv")
    out = pd.read_csv(output_path)
    return messages, history, out


def check_schema(messages, out):
    print("\n=== 1. SCHEMA & COMPLETENESS ===")
    expected_cols = ["message_id", "action", "message_type", "reason",
                      "confidence", "evidence_message_ids"]
    ok = True

    if list(out.columns) != expected_cols:
        print(f"  FAIL: column order/names wrong.\n    expected: {expected_cols}\n    got:      {list(out.columns)}")
        ok = False
    else:
        print("  PASS: columns correct and in order")

    missing = set(messages["message_id"]) - set(out["message_id"])
    extra = set(out["message_id"]) - set(messages["message_id"])
    if missing:
        print(f"  FAIL: {len(missing)} message_id(s) from messages.csv missing in output.csv")
        ok = False
    if extra:
        print(f"  FAIL: {len(extra)} message_id(s) in output.csv not present in messages.csv")
        ok = False
    if not missing and not extra and len(out) == len(messages):
        print(f"  PASS: exactly {len(out)} rows, one-to-one with messages.csv")
    else:
        ok = False

    dupes = out["message_id"].duplicated().sum()
    if dupes:
        print(f"  FAIL: {dupes} duplicate message_id rows in output.csv")
        ok = False

    valid_actions = {"notify", "digest", "mute"}
    bad_actions = set(out["action"].unique()) - valid_actions
    if bad_actions:
        print(f"  FAIL: invalid action values found: {bad_actions}")
        ok = False
    else:
        print("  PASS: all action values are valid")

    return ok


def check_evidence_namespace(messages, history, out):
    print("\n=== 2. EVIDENCE ID NAMESPACE (must cite message_history.csv only) ===")
    msg_ids = set(messages["message_id"].astype(str))
    hist_ids = set(history["message_id"].astype(str))

    total, invalid_current_batch, invalid_unknown, none_count = 0, 0, 0, 0
    for ev in out["evidence_message_ids"]:
        ev = str(ev).strip()
        if ev.lower() == "none" or ev == "" or ev == "nan":
            none_count += 1
            continue
        for part in ev.split(";"):
            part = part.strip()
            total += 1
            if part in msg_ids:
                invalid_current_batch += 1
            elif part not in hist_ids:
                invalid_unknown += 1

    print(f"  Total evidence citations: {total}")
    print(f"  Rows using 'none': {none_count}")
    print(f"  INVALID — citing current-batch messages.csv IDs: {invalid_current_batch}")
    print(f"  INVALID — citing IDs not found anywhere: {invalid_unknown}")

    ok = invalid_current_batch == 0 and invalid_unknown == 0
    print("  PASS" if ok else "  FAIL", "- evidence citations are clean" if ok else "- fix retrieval namespace filtering")
    return ok


def check_duplicate_evidence_sets(out):
    print("\n=== 3. EVIDENCE SET DIVERSITY (are different messages getting identical evidence?) ===")
    counts = out["evidence_message_ids"].value_counts()
    dupes = counts[(counts > 1) & (counts.index.str.lower() != "none")]
    if len(dupes):
        print(f"  {len(dupes)} evidence sets reused across multiple messages (verify these are genuinely similar):")
        print(dupes.to_string())
    else:
        print("  No exact-duplicate evidence sets found across different messages")
    return True  # informational, not a hard fail — needs human judgment


def check_confidence_calibration(out):
    print("\n=== 4. CONFIDENCE CALIBRATION (the metric that got gamed twice already) ===")
    desc = out["confidence"].describe()
    print(desc.to_string())

    print("\n  Distinct confidence values per message_type (THE key check):")
    per_type = out.groupby("message_type")["confidence"].nunique()
    print(per_type.to_string())

    flat_types = per_type[per_type == 1]
    flat_rows = out[out["message_type"].isin(flat_types.index)]
    flat_type_row_counts = flat_rows["message_type"].value_counts()

    ok = True
    for t in flat_types.index:
        n_rows = flat_type_row_counts.get(t, 0)
        if n_rows > 3:
            print(f"  FAIL: message_type '{t}' has {n_rows} rows but only 1 distinct confidence value "
                  f"— this is a lookup table, not calibration, unless every row has identical evidence strength")
            ok = False

    if out["confidence"].std() < 0.10:
        print(f"  FAIL: overall confidence std ({out['confidence'].std():.4f}) is too low — near-flat confidence")
        ok = False

    digest_mean = out.loc[out["action"] == "digest", "confidence"].mean()
    risky_mean = out.loc[out["message_type"].isin(["scam", "spam"]), "confidence"].mean()
    print(f"\n  digest mean confidence: {digest_mean:.3f}")
    print(f"  scam/spam mean confidence: {risky_mean:.3f}")
    if pd.notna(digest_mean) and pd.notna(risky_mean) and digest_mean >= risky_mean:
        print("  FAIL: digest (ambiguous) confidence should be lower than scam/spam confidence")
        ok = False

    print("\n  " + ("PASS" if ok else "FAIL") + " overall calibration check")
    return ok


def check_reason_quality(out):
    print("\n=== 5. REASON QUALITY (checking for placeholder / templated text) ===")
    total = len(out)

    placeholder_terms = ["UNKNOWN", "unknown_sender", "N/A", "null", "None"]
    placeholder_hits = out["reason"].str.contains("|".join(placeholder_terms), case=False, na=False).sum()
    print(f"  Rows with placeholder/unresolved identity text: {placeholder_hits} / {total} "
          f"({placeholder_hits/total*100:.1f}%)")

    raw_unique = out["reason"].nunique()
    print(f"  Raw reason uniqueness: {raw_unique} / {total} ({raw_unique/total*100:.1f}%)")

    stripped = out.apply(lambda r: str(r["reason"]).replace(str(r["message_id"]), ""), axis=1)
    stripped_unique = stripped.nunique()
    print(f"  Reason uniqueness with message_id stripped out: {stripped_unique} / {total} "
          f"({stripped_unique/total*100:.1f}%)  <- the number that actually matters")

    ok = True
    if placeholder_hits > total * 0.10:
        print("  FAIL: too many unresolved identity placeholders")
        ok = False
    if stripped_unique / total < 0.40:
        print("  FAIL: reasons are still templated once you remove the message_id crutch")
        ok = False
    print("  " + ("PASS" if ok else "FAIL"))
    return ok


def check_confidence_range(out):
    print("\n=== 6. CONFIDENCE RANGE SANITY ===")
    ok = True
    if out["confidence"].min() < 0 or out["confidence"].max() > 1:
        print("  FAIL: confidence out of [0,1] range")
        ok = False
    else:
        print(f"  PASS: confidence within [0,1], range [{out['confidence'].min():.2f}, {out['confidence'].max():.2f}]")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="dataset", help="path to dataset/ folder")
    ap.add_argument("--output", default="output/output.csv", help="path to output.csv")
    args = ap.parse_args()

    messages, history, out = load(args.dataset, args.output)

    results = {
        "schema_and_completeness": check_schema(messages, out),
        "evidence_namespace": check_evidence_namespace(messages, history, out),
        "evidence_diversity": check_duplicate_evidence_sets(out),
        "confidence_calibration": check_confidence_calibration(out),
        "reason_quality": check_reason_quality(out),
        "confidence_range": check_confidence_range(out),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        print(f"  {'PASS' if passed else 'FAIL'} - {name}")

    if all(results.values()):
        print("\nAll checks passed. Still worth spot-checking 5-10 rows by hand before submitting.")
        sys.exit(0)
    else:
        print("\nSome checks failed — do not submit yet.")
        sys.exit(1)


if __name__ == "__main__":
    main()
