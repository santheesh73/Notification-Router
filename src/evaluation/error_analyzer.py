"""Error Analysis & Confusion Matrix Generator for WhatsApp Notification Router.

Generates:
- reports/confusion_matrix.csv
- reports/classification_errors.csv
- reports/per_class_accuracy.csv
- reports/decision_statistics.json
"""

import json
from pathlib import Path
from typing import Any
import pandas as pd
from config.settings import PROJECT_ROOT
from src.utils.logger import logger

REPORTS_DIR = PROJECT_ROOT / "reports"


class ErrorAnalyzer:
    """Automated error analysis and metrics evaluator for prediction output vs ground truth."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir: Path = reports_dir or REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self, truth_csv: Path, pred_csv: Path) -> dict[str, Any]:
        """Analyze prediction quality against ground truth dataset."""
        df_truth = pd.read_csv(truth_csv)
        df_pred = pd.read_csv(pred_csv)

        merged = df_truth.merge(df_pred, on="message_id", suffixes=("_true", "_pred"))
        total = len(merged)

        if total == 0:
            logger.warning("ErrorAnalyzer: No matching message_ids found between truth and predictions.")
            return {}

        action_correct = (merged["action_true"] == merged["action_pred"]).sum()
        type_correct = (merged["message_type_true"] == merged["message_type_pred"]).sum()

        action_acc = round((action_correct / total) * 100.0, 2)
        type_acc = round((type_correct / total) * 100.0, 2)

        # 1. Generate Classification Errors Detail CSV
        error_rows = []
        for _, row in merged.iterrows():
            is_action_err = row["action_true"] != row["action_pred"]
            is_type_err = row["message_type_true"] != row["message_type_pred"]

            if is_action_err or is_type_err:
                error_rows.append({
                    "message_id": row["message_id"],
                    "action_true": row["action_true"],
                    "action_pred": row["action_pred"],
                    "type_true": row["message_type_true"],
                    "type_pred": row["message_type_pred"],
                    "confidence": row.get("confidence", 0.0),
                    "reason": row.get("reason", ""),
                    "evidence_ids": row.get("evidence_message_ids", ""),
                    "message_text": str(row.get("message_text", ""))[:150],
                    "root_cause": self._determine_root_cause(row),
                })

        df_errors = pd.DataFrame(error_rows)
        err_csv_path = self.reports_dir / "classification_errors.csv"
        df_errors.to_csv(err_csv_path, index=False)

        # 2. Per-Class Accuracy
        type_stats = []
        all_types = sorted(list(set(merged["message_type_true"].unique()).union(set(merged["message_type_pred"].unique()))))

        for t in all_types:
            sub = merged[merged["message_type_true"] == t]
            cnt = int(len(sub))
            if cnt > 0:
                c_correct = int((sub["message_type_pred"] == t).sum())
                c_acc = round((c_correct / cnt) * 100.0, 1)
            else:
                c_correct = 0
                c_acc = 0.0

            type_stats.append({
                "message_type": str(t),
                "total_true_instances": cnt,
                "correct_predictions": c_correct,
                "accuracy_pct": float(c_acc),
            })

        df_per_class = pd.DataFrame(type_stats)
        per_class_csv_path = self.reports_dir / "per_class_accuracy.csv"
        df_per_class.to_csv(per_class_csv_path, index=False)

        # 3. Action & Type Confusion Matrix CSV
        cm_action = pd.crosstab(merged["action_true"], merged["action_pred"], rownames=["True Action"], colnames=["Pred Action"])
        cm_type = pd.crosstab(merged["message_type_true"], merged["message_type_pred"], rownames=["True Type"], colnames=["Pred Type"])

        cm_csv_path = self.reports_dir / "confusion_matrix.csv"
        with open(cm_csv_path, mode="w", encoding="utf-8") as f:
            f.write("=== ACTION CONFUSION MATRIX ===\n")
            cm_action.to_csv(f)
            f.write("\n=== MESSAGE TYPE CONFUSION MATRIX ===\n")
            cm_type.to_csv(f)

        # 4. Overall Decision Statistics JSON
        stats_data = {
            "total_messages_evaluated": total,
            "action_accuracy_pct": action_acc,
            "message_type_accuracy_pct": type_acc,
            "total_errors": len(error_rows),
            "action_error_count": int(total - action_correct),
            "message_type_error_count": int(total - type_correct),
            "per_class_accuracy": type_stats,
        }

        stats_json_path = self.reports_dir / "decision_statistics.json"
        with open(stats_json_path, mode="w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2)

        logger.info(f"Error Analysis complete: Action Acc={action_acc}%, Message Type Acc={type_acc}%")
        return stats_data

    def _determine_root_cause(self, row: pd.Series) -> str:
        """Determine human-readable root cause for a classification error."""
        t_true = str(row["message_type_true"])
        t_pred = str(row["message_type_pred"])
        a_true = str(row["action_true"])
        a_pred = str(row["action_pred"])

        if t_pred == "scam" and t_true != "scam":
            return "Over-aggressive scam detection on legitimate message/link."
        if t_pred == "business_update" and t_true != "business_update":
            return f"Broad business update keyword match overrode true '{t_true}' intent."
        if t_true == "urgent" and a_pred != "notify":
            return "Failed to detect time-sensitive urgency or temporal deadline constraint."
        if t_true == "event" and t_pred != "event":
            return "Event schedule/calendar keyword missed by rule engine."
        if t_true == "promotion" and t_pred != "promotion":
            return "Marketing/commercial offer features not detected."
        if a_true != a_pred:
            return f"Action mismatch ({a_pred} vs {a_true}) due to rule priority ranking."

        return f"Message type misclassified as '{t_pred}' instead of '{t_true}'."
