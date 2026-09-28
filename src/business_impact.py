"""Financial impact calculations."""

from __future__ import annotations

import pandas as pd


def calculate_business_impact(tickets: pd.DataFrame, cost_per_breach: float = 350.0, target_breach_rate: float = 15.0, tickets_per_week: int = 650) -> pd.DataFrame:
    """Estimate loss and savings at current and target breach rates."""
    valid = tickets[tickets["sla_breach"].isin(("Yes", "No"))]
    current_rate = float((valid["sla_breach"] == "Yes").mean() * 100) if len(valid) else 0.0
    monthly_tickets = tickets_per_week * 52 / 12
    current_monthly = monthly_tickets * current_rate / 100 * cost_per_breach
    target_monthly = monthly_tickets * target_breach_rate / 100 * cost_per_breach
    return pd.DataFrame([{
        "current_breach_rate_pct": round(current_rate, 2), "target_breach_rate_pct": target_breach_rate,
        "reduction_pct_points": round(max(current_rate - target_breach_rate, 0), 2),
        "cost_per_breached_ticket": cost_per_breach, "monthly_loss": round(current_monthly, 2),
        "quarterly_loss": round(current_monthly * 3, 2), "annual_loss": round(current_monthly * 12, 2),
        "monthly_savings_at_target": round(max(current_monthly - target_monthly, 0), 2),
        "quarterly_savings_at_target": round(max(current_monthly - target_monthly, 0) * 3, 2),
        "annual_savings_at_target": round(max(current_monthly - target_monthly, 0) * 12, 2),
    }])
