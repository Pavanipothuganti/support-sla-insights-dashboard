"""Agent-level SLA summaries."""

from __future__ import annotations

import pandas as pd


def _agent_column(tickets: pd.DataFrame) -> str:
    for name in ("agent_name", "agent", "assigned_agent", "agent_id"):
        if name in tickets.columns:
            return name
    raise ValueError("No agent column found in tickets.csv")


def analyse_agents(tickets: pd.DataFrame) -> pd.DataFrame:
    agent_column = _agent_column(tickets)
    working = tickets[tickets["sla_breach"].isin(("Yes", "No"))].copy()
    report = working.groupby(agent_column, dropna=False).agg(
        total_tickets=("sla_breach", "size"),
        breached_tickets=("sla_breach", lambda values: int((values == "Yes").sum())),
        average_response_hours=("first_response_hours", "mean"),
    ).reset_index().rename(columns={agent_column: "agent"})
    report["breach_percentage"] = (report["breached_tickets"] / report["total_tickets"] * 100).round(2)
    return report.sort_values(["breached_tickets", "breach_percentage"], ascending=False).reset_index(drop=True)
