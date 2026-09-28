"""Lightweight reproducible validation checks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def validate_results(tickets: pd.DataFrame, sample_size: int = 50, seed: int = 42) -> dict[str, object]:
    valid = tickets[tickets["sla_breach"].isin(("Yes", "No"))].copy()
    sample = valid.sample(min(sample_size, len(valid)), random_state=seed) if len(valid) else valid
    targets = tickets.attrs.get("sla_targets", {})
    sample_targets = sample["channel"].astype("string").str.lower().map(targets)
    expected = sample["first_response_hours"].gt(sample_targets).map({True: "Yes", False: "No"})
    expected = expected.mask(sample_targets.isna(), "Unknown")
    mismatches = int((sample["sla_breach"] != expected).sum()) if len(sample) else 0
    return {
        "rows_checked": int(len(valid)), "random_sample_size": int(len(sample)), "sample_mismatches": mismatches,
        "sample_accuracy_pct": round((1 - mismatches / len(sample)) * 100, 2) if len(sample) else None,
        "unknown_sla_rows": int((tickets["sla_breach"] == "Unknown").sum()),
        "negative_response_rows": int((tickets["first_response_hours"] < 0).sum()),
    }


def write_validation_report(report: dict[str, object], issues: list[str], output_path: str | Path) -> None:
    lines = ["Support SLA validation report", "=" * 30]
    lines.extend(f"{key}: {value}" for key, value in report.items())
    lines.append("\nData quality issues")
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("None")
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
