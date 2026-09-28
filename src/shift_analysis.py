"""Shift-level SLA summaries using roster data when available."""

from __future__ import annotations

import pandas as pd


def _merge_shift(tickets: pd.DataFrame, agents: pd.DataFrame | None) -> pd.DataFrame:
    result = tickets.copy()
    if "shift" in result.columns:
        return result
    if agents is None or "shift" not in agents.columns:
        result["shift"] = "Unknown"
        return result
    ticket_key = next((key for key in ("agent_id", "agent", "agent_name") if key in result.columns), None)
    agent_key = next((key for key in ("agent_id", "agent", "agent_name") if key in agents.columns), None)
    if not ticket_key or not agent_key:
        result["shift"] = "Unknown"
        return result

    if {"from_date", "to_date"}.issubset(agents.columns):
        created_column = next(
            (key for key in ("created_at_normalized", "created_at", "created_date", "ticket_created_at", "opened_at") if key in result.columns),
            None,
        )
        if created_column is None:
            result["shift"] = "Unknown"
            return result

        ticket_dates = pd.to_datetime(result[created_column], errors="coerce", utc=True)
        ticket_dates = ticket_dates.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None).dt.normalize()
        roster = agents[[agent_key, "shift", "from_date", "to_date"]].copy()
        roster["_from_date"] = pd.to_datetime(roster["from_date"], errors="coerce").dt.normalize()
        roster["_to_date"] = pd.to_datetime(roster["to_date"], errors="coerce").dt.normalize()
        roster = roster.rename(columns={agent_key: ticket_key})

        indexed = result.reset_index(drop=True).copy()
        indexed["_ticket_row"] = range(len(indexed))
        indexed["_ticket_date"] = ticket_dates.reset_index(drop=True)
        candidates = indexed[["_ticket_row", "_ticket_date", ticket_key]].merge(roster, on=ticket_key, how="left")
        active = candidates[
            candidates["_ticket_date"].notna()
            & candidates["_from_date"].notna()
            & (candidates["_ticket_date"] >= candidates["_from_date"])
            & (candidates["_to_date"].isna() | (candidates["_ticket_date"] <= candidates["_to_date"]))
        ]
        unique_assignments = active.drop_duplicates("_ticket_row", keep=False).set_index("_ticket_row")["shift"]
        result["shift"] = pd.Series(range(len(result))).map(unique_assignments).fillna("Unknown").to_numpy()
        return result

    roster = agents[[agent_key, "shift"]].drop_duplicates(agent_key).rename(columns={agent_key: ticket_key})
    return result.merge(roster, on=ticket_key, how="left").assign(shift=lambda frame: frame["shift"].fillna("Unknown"))


def analyse_shifts(tickets: pd.DataFrame, agents: pd.DataFrame | None = None) -> pd.DataFrame:
    working = _merge_shift(tickets, agents)
    working = working[working["sla_breach"].isin(("Yes", "No"))]
    report = working.groupby("shift", dropna=False).agg(
        total_tickets=("sla_breach", "size"),
        breached_tickets=("sla_breach", lambda values: int((values == "Yes").sum())),
    ).reset_index()
    report["breach_percentage"] = (report["breached_tickets"] / report["total_tickets"] * 100).round(2)
    return report.sort_values("breach_percentage", ascending=False).reset_index(drop=True)
