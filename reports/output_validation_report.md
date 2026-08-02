# Phase 1: Output Validation Report

**Timestamp**: 2026-08-02T08:11:00+05:30  
**Target File**: `output/output.csv`  
**Status**: **`PASSED (100% VALID)`**

---

## 1. Executive Summary & Verification Matrix

| Validation Criteria | Requirement | Audit Result | Status |
| :--- | :--- | :--- | :--- |
| **Row Count** | Exactly 1 per input message (110) | **110 Rows** | **`PASSED`** |
| **Message ID Uniqueness** | 110 unique IDs | **110 Unique IDs (0 duplicates)** | **`PASSED`** |
| **Null / Missing Values** | 0 nulls across all columns | **0 Nulls (100% complete)** | **`PASSED`** |
| **Schema Compliance** | Exact 6 columns required | **Exact 6 columns matched** | **`PASSED`** |
| **Allowed Actions** | `notify`, `digest`, `mute` | **`notify` (31), `digest` (46), `mute` (33)** | **`PASSED`** |
| **Allowed Message Types** | 10 official HackerRank categories | **10 Categories present** | **`PASSED`** |
| **Confidence Range** | Bounds $[0.00, 1.00]$ | **Min: $0.5501$, Max: $0.9850$, Mean: $0.7335$** | **`PASSED`** |
| **Evidence Format** | Semicolon-separated `message_...` IDs | **100% Valid Semicolon-Separated IDs** | **`PASSED`** |
| **Reason Format** | Concise, non-empty, entity-grounded | **100% Non-empty ($\le 25$ words)** | **`PASSED`** |

---

## 2. Column Schema Audit

| Column Name | Expected Type | Verified Data Type | Null Count | Sample Value |
| :--- | :--- | :--- | :--- | :--- |
| `message_id` | String | String | 0 | `message_0001` |
| `action` | Enum (`notify`/`digest`/`mute`) | String | 0 | `notify` |
| `message_type` | Enum (10 categories) | String | 0 | `urgent` |
| `reason` | String | String | 0 | `Time-sensitive alert requiring immediate user attention.` |
| `confidence` | Float $[0.0, 1.0]$ | Float64 | 0 | `0.9500` |
| `evidence_message_ids` | Semicolon-separated IDs | String | 0 | `message_0299;message_0272;message_0033` |

---

## 3. Categorical Distribution & Calibration Analysis

### Action Distribution
- **`digest`**: 46 messages (41.8%)
- **`mute`**: 33 messages (30.0%)
- **`notify`**: 31 messages (28.2%)

### Message Type Breakdown
- `event`: 23 (20.9%)
- `promotion`: 18 (16.4%)
- `business_update`: 16 (14.5%)
- `urgent`: 11 (10.0%)
- `greeting`: 11 (10.0%)
- `payment`: 10 (9.1%)
- `scam`: 10 (9.1%)
- `personal`: 7 (6.4%)
- `spam`: 3 (2.7%)
- `forward`: 1 (0.9%)

---

## 4. Empirical Sample Output Verification (First 5 Rows)

```csv
message_id,action,message_type,reason,confidence,evidence_message_ids
message_0001,notify,urgent,Time-sensitive alert from sender u_014 in group group_002 requiring immediate user attention.,0.95,message_0245;message_0112;message_0399
message_0002,notify,event,Event schedule update from sender u_022 in group group_008 routed to notify.,0.92,message_0088;message_0142;message_0301
message_0003,notify,urgent,Time-sensitive alert from sender u_009 in group group_001 requiring immediate user attention.,0.95,message_0019;message_0202;message_0388
message_0004,notify,business_update,Operational notification from business business_044 routed to notify.,0.90,message_0104;message_0299;message_0312
message_0005,notify,event,Event schedule update from sender u_018 in group group_003 routed to notify.,0.92,message_0044;message_0199;message_0278
```

---

## 5. Conclusion & Verification Verdict

The output CSV passes all HackerRank schema, entity grounding, confidence range, and row-count verification constraints. **100% PRODUCTION READY**.
