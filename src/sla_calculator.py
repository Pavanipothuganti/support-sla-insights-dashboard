"""First-response SLA parsing and calculation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

import pandas as pd

DEFAULT_SLA_TARGETS = {"chat": 0.25, "voice": 2.0, "social": 4.0, "email": 8.0}


def read_sla_targets(policy_path: str | Path = "data/support-policy.pdf") -> dict[str, float]:
    """Extract channel-specific first-response targets, with transparent fallbacks."""
    try:
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(policy_path)).pages)
    except (ImportError, OSError, ValueError, AttributeError):
        return DEFAULT_SLA_TARGETS.copy()

    targets_text = re.search(r"Targets:\s*(.*?)(?:Every ticket|$)", text, flags=re.IGNORECASE | re.DOTALL)
    if not targets_text:
        return DEFAULT_SLA_TARGETS.copy()

    targets = DEFAULT_SLA_TARGETS.copy()
    labels = {"chat": "chat", "voice": r"voice\s+callback", "social": "social", "email": "email"}
    for channel, label in labels.items():
        match = re.search(
            rf"{label}\s+([0-9]+(?:\.[0-9]+)?)\s*(hour|hr|minute|min)s?",
            targets_text.group(1),
            flags=re.IGNORECASE,
        )
        if match:
            value = float(match.group(1))
            targets[channel] = value / 60 if match.group(2).lower().startswith("min") else value
    return targets


def _find_column(frame: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    return next((column for column in candidates if column in frame.columns), None)


def calculate_sla(tickets: pd.DataFrame, sla_targets: Mapping[str, float]) -> pd.DataFrame:
    """Return tickets with response hours, week, and Yes/No breach flags."""
    result = tickets.copy()
    created_column = _find_column(result, ("created_at", "created_date", "ticket_created_at", "opened_at"))
    response_column = _find_column(result, ("first_response_at", "response_at", "first_response_time"))
    if not created_column or not response_column:
        raise ValueError("tickets.csv needs creation and first-response timestamp columns")
    if "channel" not in result.columns:
        raise ValueError("tickets.csv needs a channel column for channel-specific SLA targets")
    created = pd.to_datetime(result[created_column], errors="coerce", utc=True)
    if response_column == "first_response_time":
        response_hours = pd.to_numeric(result[response_column], errors="coerce")
    else:
        responded = pd.to_datetime(result[response_column], errors="coerce", utc=True)
        response_hours = (responded - created).dt.total_seconds() / 3600
    result["created_at_normalized"] = created
    result["first_response_hours"] = response_hours.round(3)
    result["sla_target_hours"] = result["channel"].astype("string").str.lower().map(sla_targets)
    result["sla_breach"] = result["first_response_hours"].gt(result["sla_target_hours"]).map({True: "Yes", False: "No"})
    result.loc[result["first_response_hours"].isna() | result["sla_target_hours"].isna(), "sla_breach"] = "Unknown"
    local_created = created.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    result["week"] = local_created.dt.to_period("W").astype("string")
    return result
