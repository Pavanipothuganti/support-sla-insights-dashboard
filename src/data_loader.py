"""Load and lightly validate the source data files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

LOGGER = logging.getLogger(__name__)
CSV_FILES = ("tickets", "agents", "orders", "customers", "products")


def _normalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).strip().lower().replace(" ", "_") for column in frame.columns]
    return frame


def load_csv_data(data_dir: str | Path = "data") -> dict[str, pd.DataFrame]:
    """Load all expected CSV files, preserving available files and logging failures."""
    data_path = Path(data_dir)
    loaded: dict[str, pd.DataFrame] = {}
    for name in CSV_FILES:
        file_path = data_path / f"{name}.csv"
        try:
            if not file_path.exists():
                LOGGER.error("Missing input file: %s", file_path)
                continue
            loaded[name] = _normalise_columns(pd.read_csv(file_path)).convert_dtypes()
        except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
            LOGGER.exception("Could not load %s: %s", file_path, exc)
    return loaded


def validate_data(data: dict[str, pd.DataFrame]) -> list[str]:
    """Return human-readable data quality issues without stopping the pipeline."""
    issues: list[str] = []
    if "tickets" not in data or data["tickets"].empty:
        issues.append("tickets.csv is missing or empty")
        return issues
    ticket_columns = set(data["tickets"].columns)
    if not ticket_columns.intersection({"created_at", "created_date", "ticket_created_at", "opened_at"}):
        issues.append("tickets.csv has no recognised creation timestamp column")
    if not ticket_columns.intersection({"first_response_at", "first_response_time", "response_at"}):
        issues.append("tickets.csv has no recognised first-response column")
    if not ticket_columns.intersection({"agent_id", "agent", "assigned_agent", "agent_name"}):
        issues.append("tickets.csv has no recognised agent column")
    for name, frame in data.items():
        if frame.empty:
            issues.append(f"{name}.csv is empty")
        duplicated = int(frame.duplicated().sum())
        if duplicated:
            issues.append(f"{name}.csv contains {duplicated} duplicate rows")
    return issues


def data_quality_summary(data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Summarise row counts and missing values for the validation report."""
    return {name: {"rows": int(frame.shape[0]), "columns": int(frame.shape[1]), "missing_cells": int(frame.isna().sum().sum())} for name, frame in data.items()}
