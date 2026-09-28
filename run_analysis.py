"""Generate all reports from the source files in data/."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.agent_analysis import analyse_agents
from src.business_impact import calculate_business_impact
from src.data_loader import data_quality_summary, load_csv_data, validate_data
from src.shift_analysis import analyse_shifts
from src.sla_calculator import calculate_sla, read_sla_targets
from src.validation import validate_results, write_validation_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def run(data_dir: str | Path = "data", reports_dir: str | Path = "reports", cost_per_breach: float = 350.0, target_rate: float = 15.0):
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    data = load_csv_data(data_dir)
    if "tickets" not in data:
        raise FileNotFoundError("Place tickets.csv in the data/ directory before running the analysis")
    duplicate_ids_removed = 0
    if "ticket_id" in data["tickets"].columns:
        duplicate_ids_removed = int(data["tickets"]["ticket_id"].duplicated().sum())
        data["tickets"] = data["tickets"].drop_duplicates("ticket_id", keep="first")
    issues = validate_data(data)
    if duplicate_ids_removed:
        issues.append(f"tickets.csv: removed {duplicate_ids_removed} repeated ticket_id rows")
    sla_targets = read_sla_targets(Path(data_dir) / "support-policy.pdf")
    tickets = calculate_sla(data["tickets"], sla_targets)
    tickets.attrs["sla_targets"] = sla_targets
    valid = tickets[tickets["sla_breach"].isin(("Yes", "No"))]
    weekly = valid.groupby("week", dropna=False).agg(
        total_tickets=("sla_breach", "size"),
        breaches=("sla_breach", lambda values: int((values == "Yes").sum())),
    ).reset_index()
    weekly["breach_rate_pct"] = (weekly["breaches"] / weekly["total_tickets"] * 100).round(2)
    weekly.to_csv(reports / "weekly_sla_report.csv", index=False)
    analyse_agents(tickets).to_csv(reports / "agent_performance_report.csv", index=False)
    analyse_shifts(tickets, data.get("agents")).to_csv(reports / "shift_performance_report.csv", index=False)
    calculate_business_impact(tickets, cost_per_breach, target_rate).to_csv(reports / "business_impact_report.csv", index=False)
    validation = validate_results(tickets)
    validation["sla_target_hours_by_channel"] = sla_targets
    validation["duplicate_ticket_ids_removed"] = duplicate_ids_removed
    validation["source_summary"] = data_quality_summary(data)
    write_validation_report(validation, issues, reports / "validation_report.txt")
    tickets.to_csv(reports / "ticket_sla_detail.csv", index=False)
    return validation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--cost-per-breach", type=float, default=350.0)
    parser.add_argument("--target-rate", type=float, default=15.0)
    args = parser.parse_args()
    run(args.data_dir, args.reports_dir, args.cost_per_breach, args.target_rate)
