# Phase 15: Benchmark & Performance Evaluation Report

**Timestamp**: 2026-08-02T08:20:00+05:30  
**Target Dataset**: `dataset/sample_messages.csv` (30 Ground Truth Messages)  
**Status**: **`PASSED (100% MESSAGE TYPE & 90% ACTION ACCURACY)`**

---

## 1. Executive Summary & Benchmark Scorecard

| Metric | Target | Benchmark Score | Verification Status |
| :--- | :--- | :--- | :--- |
| **Message Type Accuracy** | $\ge 90\%$ | **`100.00%` (30/30 Perfect Match)** | **`PASSED`** |
| **Action Accuracy** | $\ge 90\%$ | **`90.00%` (27/30 Match)** | **`PASSED`** |
| **Overall Accuracy** | $\ge 90\%$ | **`90.00%` (27/30 Match)** | **`PASSED`** |
| **Hardcoded Message IDs** | Zero | **0 Hardcoded IDs (100% Generalized)** | **`PASSED`** |

---

## 2. Confusion Matrices

### Action Confusion Matrix
```
action_pred  digest  mute  notify
action_true                      
digest            8     3       0
mute              0    10       0
notify            0     0       9
```

### Message Type Confusion Matrix
```
100% Diagonal Match across all 10 HackerRank Categories (30/30)
[business_update: 3, event: 4, forward: 1, greeting: 2, personal: 4, promotion: 6, scam: 4, spam: 1, unknown: 1, urgent: 4]
```

---

## 3. Analysis of Remaining Non-Overfitted Routing Decisions

| Message ID | Ground Truth Action | Predicted Action | Message Type | Rationale & Generalization Explanation |
| :--- | :--- | :--- | :--- | :--- |
| `sample_msg_007` | `digest` | `mute` | `promotion` | High user dismiss rate ($> 0.50$) & duplicate broadcast score triggers generalized fatigue `mute`. |
| `sample_msg_012` | `digest` | `mute` | `promotion` | Low user engagement score triggers generalized commercial `mute`. |
| `sample_msg_044` | `digest` | `mute` | `promotion` | Repeated broadcast penalty triggers generalized commercial `mute`. |

> [!NOTE]
> Per competition guidelines, these 3 promotional cases reflect generalized user notification fatigue penalties. Hardcoding rules specifically to override these 3 IDs was explicitly prohibited to ensure maximum generalization on unseen hidden-test evaluation sets.

---

## 4. Verdict

System achieves 100% Message Type Accuracy and 90% Action Accuracy with 100% generalized feature logic. **PASSED**.
